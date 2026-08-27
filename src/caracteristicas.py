import os

import numpy as np
from PIL import Image, ImageFile
from scipy import ndimage

from src.config import (
    DIR_IMAGENES,
    DIR_PROCESADO,
    EXTENSIONES_IMAGEN,
    LADO_MINIATURA,
    UMBRAL_SOBREEXPUESTO,
    UMBRAL_SUBEXPUESTO,
)

ImageFile.LOAD_TRUNCATED_IMAGES = True
Image.MAX_IMAGE_PIXELS = None

RUTA_CACHE = DIR_PROCESADO / "caracteristicas_imagenes.parquet"
ETIQUETAS_EXIF = {271: "marca", 272: "modelo", 274: "orientacion", 306: "fecha_captura"}


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
