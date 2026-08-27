import argparse
import multiprocessing
import os

import numpy as np
import pandas as pd
from PIL import Image, ImageFile
from scipy import ndimage
from tqdm import tqdm

from src.config import (
    DIR_IMAGENES,
    DIR_PROCESADO,
    DISTANCIA_HAMMING_MAXIMA,
    EXTENSIONES_IMAGEN,
    LADO_MINIATURA,
    UMBRAL_SOBREEXPUESTO,
    UMBRAL_SUBEXPUESTO,
)

ImageFile.LOAD_TRUNCATED_IMAGES = True
Image.MAX_IMAGE_PIXELS = None

RUTA_CACHE = DIR_PROCESADO / "caracteristicas_imagenes.parquet"
ETIQUETAS_EXIF = {271: "marca", 272: "modelo", 274: "orientacion", 306: "fecha_captura"}
TAMANO_BLOQUE_MAXIMO = 500


def leer_exif(imagen):
    resultado = {clave: None for clave in ETIQUETAS_EXIF.values()}
    try:
        datos = imagen.getexif()
        if not datos:
            return resultado
        for codigo, clave in ETIQUETAS_EXIF.items():
            valor = datos.get(codigo)
            if valor is None:
                continue
            if isinstance(valor, bytes):
                valor = valor.decode("utf-8", errors="ignore")
            if isinstance(valor, str):
                valor = valor.strip("\x00").strip()
            resultado[clave] = valor
    except Exception:
        pass
    return resultado


def calcular_hash_perceptual(gris):
    reducido = Image.fromarray(gris.astype("uint8")).resize((9, 8), Image.BILINEAR)
    valores = np.asarray(reducido, dtype=np.int16)
    diferencias = valores[:, :-1] > valores[:, 1:]
    cadena_bits = "".join("1" if v else "0" for v in diferencias.flatten())
    return format(int(cadena_bits, 2), "016x")


def describir_imagen(ruta_relativa):
    resultado = {"ruta_relativa": ruta_relativa, "error": None}
    ruta_absoluta = DIR_IMAGENES / ruta_relativa
    try:
        resultado["peso_kb"] = round(ruta_absoluta.stat().st_size / 1024, 2)
        with Image.open(ruta_absoluta) as imagen:
            ancho, alto = imagen.size
            resultado["ancho"], resultado["alto"] = ancho, alto
            resultado["formato"], resultado["modo"] = imagen.format, imagen.mode
            resultado.update(leer_exif(imagen))
            imagen.draft(None, (LADO_MINIATURA, LADO_MINIATURA))
            miniatura = imagen.convert("RGB")
            miniatura.thumbnail((LADO_MINIATURA, LADO_MINIATURA), Image.BILINEAR)

        arreglo = np.asarray(miniatura, dtype=np.float64)
        r, g, b = arreglo[..., 0], arreglo[..., 1], arreglo[..., 2]
        gris = r * 0.299 + g * 0.587 + b * 0.114

        resultado["aspecto"] = round(ancho / alto, 4) if alto else None
        resultado["megapixeles"] = round(ancho * alto / 1_000_000, 4)
        resultado["vertical"] = alto > ancho
        resultado["media_r"] = float(r.mean())
        resultado["media_g"] = float(g.mean())
        resultado["media_b"] = float(b.mean())

        maximo = arreglo.max(axis=-1)
        minimo = arreglo.min(axis=-1)
        saturacion_pixel = np.divide(
            maximo - minimo, maximo, out=np.zeros_like(maximo), where=maximo != 0
        )
        resultado["saturacion"] = float(saturacion_pixel.mean())

        suma = r + g + b + 1e-6
        exceso_verde_pixel = 2 * (g / suma) - (r / suma) - (b / suma)
        resultado["exceso_verde"] = float(exceso_verde_pixel.mean())

        resultado["brillo"] = float(gris.mean())
        resultado["contraste"] = float(gris.std())
        resultado["prop_sobreexpuesta"] = float((gris >= UMBRAL_SOBREEXPUESTO).mean())
        resultado["prop_subexpuesta"] = float((gris <= UMBRAL_SUBEXPUESTO).mean())
        resultado["nitidez"] = float(ndimage.laplace(gris).var())
        resultado["hash_perceptual"] = calcular_hash_perceptual(gris)
    except Exception as error:
        resultado["error"] = f"{type(error).__name__}: {error}"
    return resultado


def listar_rutas_particion(particion):
    directorio = DIR_IMAGENES / particion
    if not directorio.exists():
        return []
    return sorted(
        f"{particion}/{ruta.name}"
        for ruta in directorio.iterdir()
        if ruta.suffix.lower() in EXTENSIONES_IMAGEN
    )


def numero_procesos(solicitado=None):
    if solicitado is not None:
        return max(1, solicitado)
    disponibles = os.cpu_count() or 1
    return max(1, min(8, disponibles - 1))


def construir_tabla(rutas, procesos=None, reanudar=True, guardar=True):
    previa = None
    pendientes = list(rutas)
    if reanudar and RUTA_CACHE.exists():
        previa = pd.read_parquet(RUTA_CACHE)
        ya_procesadas = set(previa["ruta_relativa"])
        pendientes = [r for r in rutas if r not in ya_procesadas]

    if not pendientes:
        cantidad_previa = len(previa) if previa is not None else 0
        print(f"{cantidad_previa} registros ya estaban en la cache, nada que procesar")
        return previa if previa is not None else pd.DataFrame()

    with multiprocessing.Pool(numero_procesos(procesos)) as pool:
        nuevos = list(
            tqdm(
                pool.imap(describir_imagen, pendientes),
                total=len(pendientes),
                desc="extrayendo caracteristicas",
            )
        )

    tabla_nueva = pd.DataFrame(nuevos)
    tabla = (
        pd.concat([previa, tabla_nueva], ignore_index=True)
        if previa is not None
        else tabla_nueva
    )
    tabla = tabla.sort_values("ruta_relativa", ignore_index=True)
    tabla["particion"] = tabla["ruta_relativa"].str.split("/").str[0]
    tabla["archivo"] = tabla["ruta_relativa"].str.split("/").str[-1]

    if guardar:
        DIR_PROCESADO.mkdir(parents=True, exist_ok=True)
        tabla.to_parquet(RUTA_CACHE, index=False)
    return tabla


def cargar_cache():
    if not RUTA_CACHE.exists():
        raise FileNotFoundError(
            f"No se encuentra {RUTA_CACHE}. Ejecute 'python -m src.caracteristicas' antes de "
            "continuar."
        )
    return pd.read_parquet(RUTA_CACHE)


def _hash_a_entero(hash_hex):
    if not isinstance(hash_hex, str):
        return 0
    try:
        return int(hash_hex, 16)
    except ValueError:
        return 0


class _ConjuntosDisjuntos:
    def __init__(self, n):
        self.padre = list(range(n))

    def encontrar(self, i):
        while self.padre[i] != i:
            self.padre[i] = self.padre[self.padre[i]]
            i = self.padre[i]
        return i

    def unir(self, i, j):
        raiz_i, raiz_j = self.encontrar(i), self.encontrar(j)
        if raiz_i != raiz_j:
            self.padre[raiz_i] = raiz_j


def agrupar_duplicados(hashes, distancia_maxima=DISTANCIA_HAMMING_MAXIMA):
    enteros = [_hash_a_entero(h) for h in hashes]
    conjuntos = _ConjuntosDisjuntos(len(enteros))

    # con 4 bloques de 16 bits, dos huellas a distancia de Hamming pequena comparten
    # forzosamente al menos un bloque identico (principio de casillas); esto solo
    # sostiene la busqueda si distancia_maxima se mantiene baja respecto al numero de
    # bloques, que es el caso de uso real de este dataset
    for desplazamiento in (0, 16, 32, 48):
        mascara = 0xFFFF << desplazamiento
        bloques = {}
        for indice, valor in enumerate(enteros):
            clave = (valor & mascara) >> desplazamiento
            bloques.setdefault(clave, []).append(indice)
        for indices in bloques.values():
            if len(indices) < 2 or len(indices) > TAMANO_BLOQUE_MAXIMO:
                continue
            for pos_a in range(len(indices)):
                for pos_b in range(pos_a + 1, len(indices)):
                    i, j = indices[pos_a], indices[pos_b]
                    distancia = bin(enteros[i] ^ enteros[j]).count("1")
                    if distancia <= distancia_maxima:
                        conjuntos.unir(i, j)

    mapa_grupo = {}
    grupos = []
    for indice in range(len(enteros)):
        representante = conjuntos.encontrar(indice)
        if representante not in mapa_grupo:
            mapa_grupo[representante] = len(mapa_grupo)
        grupos.append(mapa_grupo[representante])
    return grupos


def detectar_hashes_degenerados(hashes):
    # imagenes casi monocromas (tomas muy oscuras o muy sobreexpuestas) producen esta
    # huella; agruparlas entre si por hash no implica que su contenido visual sea el mismo
    serie = pd.Series(list(hashes))
    return (serie.isna() | serie.eq("0" * 16) | serie.eq("f" * 16)).to_numpy()


def resumen_duplicados(df, columna="grupo_visual"):
    tamanos = df.groupby(columna).size()
    en_grupo_multiple = tamanos[tamanos > 1]
    return pd.DataFrame(
        [
            {
                "total_imagenes": len(df),
                "grupos_totales": int(tamanos.shape[0]),
                "imagenes_en_grupo_multiple": int(en_grupo_multiple.sum()),
                "grupos_con_multiples": int((tamanos > 1).sum()),
                "tamano_grupo_mas_grande": int(tamanos.max()) if not tamanos.empty else 0,
            }
        ]
    )


def _main():
    analizador = argparse.ArgumentParser(description="Extraccion de atributos de imagen")
    analizador.add_argument("--particion", choices=("train", "test", "todas"), default="todas")
    analizador.add_argument("--procesos", type=int, default=None)
    analizador.add_argument("--limite", type=int, default=None)
    analizador.add_argument("--desde-cero", action="store_true")
    argumentos = analizador.parse_args()

    particiones = (
        ("train", "test") if argumentos.particion == "todas" else (argumentos.particion,)
    )
    rutas = []
    for particion in particiones:
        rutas.extend(listar_rutas_particion(particion))
    if argumentos.limite is not None:
        rutas = rutas[: argumentos.limite]

    if not rutas:
        print("No se encontraron imagenes. Ejecute 'python -m src.descarga todo' primero.")
        return

    tabla = construir_tabla(
        rutas, procesos=argumentos.procesos, reanudar=not argumentos.desde_cero, guardar=True
    )
    print(f"Registros en cache: {len(tabla)}")
    print(f"Imagenes con error de lectura: {int(tabla['error'].notna().sum())}")
    print(f"Cache guardada en: {RUTA_CACHE}")


if __name__ == "__main__":
    _main()
