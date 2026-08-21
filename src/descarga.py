import argparse
import shutil
import zipfile

import requests
from tqdm import tqdm

from src.config import (
    ARCHIVOS_DRIVE,
    ARCHIVOS_ZINDI,
    CARPETA_DRIVE,
    CONTEO_OFICIAL_TEMPORADA,
    DIR_CRUDO,
    DIR_IMAGENES,
    EXTENSIONES_IMAGEN,
    URL_ARCHIVOS_ZINDI,
    asegurar_directorios,
)
from src.credenciales import obtener_secreto

TAMANO_BLOQUE = 1024 * 1024
INICIOS_INVALIDOS = (b"<!doctype", b"<html", b"{\"error", b"{\"message")


def _respuesta_es_csv(ruta):
    with open(ruta, "rb") as archivo:
        inicio = archivo.read(64).lstrip().lower()
    return not inicio.startswith(INICIOS_INVALIDOS)


def descargar_csv(forzar=False):
    asegurar_directorios()
    token = obtener_secreto()
    descargados = []
    for nombre in ARCHIVOS_ZINDI:
        destino = DIR_CRUDO / nombre
        if destino.exists() and not forzar:
            print(f"{nombre} ya existe, se omite")
            descargados.append(destino)
            continue
        url = f"{URL_ARCHIVOS_ZINDI}/{nombre}"
        with requests.get(url, params={"auth_token": token}, stream=True, timeout=60) as respuesta:
            respuesta.raise_for_status()
            total = int(respuesta.headers.get("content-length", 0))
            temporal = destino.with_suffix(destino.suffix + ".parcial")
            with open(temporal, "wb") as archivo:
                barra = tqdm(total=total, unit="B", unit_scale=True, desc=nombre)
                for bloque in respuesta.iter_content(chunk_size=TAMANO_BLOQUE):
                    archivo.write(bloque)
                    barra.update(len(bloque))
                barra.close()
        if not _respuesta_es_csv(temporal):
            temporal.unlink()
            raise RuntimeError(
                f"La respuesta para {nombre} no es un CSV valido. Verifique que el token de "
                "Zindi sea correcto y que haya aceptado los terminos de la competencia. "
                "Use 'python -m src.credenciales borrar' para reemplazarlo."
            )
        temporal.replace(destino)
        descargados.append(destino)
    return descargados


def descargar_imagenes(forzar=False):
    import gdown

    asegurar_directorios()
    faltantes = [n for n in ARCHIVOS_DRIVE if forzar or not (DIR_CRUDO / n).exists()]
    if not faltantes:
        print("Los archivos comprimidos ya estan descargados")
        return [DIR_CRUDO / n for n in ARCHIVOS_DRIVE]
    gdown.download_folder(
        url=CARPETA_DRIVE,
        output=str(DIR_CRUDO),
        quiet=False,
        use_cookies=False,
        resume=True,
    )
    ausentes = [n for n in ARCHIVOS_DRIVE if not (DIR_CRUDO / n).exists()]
    if ausentes:
        raise RuntimeError(
            f"No se descargaron los archivos {', '.join(ausentes)}. Google Drive limita la "
            f"descarga masiva por cuota. Descarguelos manualmente desde {CARPETA_DRIVE} "
            f"y coloquelos en {DIR_CRUDO}."
        )
    return [DIR_CRUDO / n for n in ARCHIVOS_DRIVE]


def extraer(nombre_zip, forzar=False):
    origen = DIR_CRUDO / nombre_zip
    if not origen.exists():
        raise FileNotFoundError(f"No se encuentra {origen}")
    destino = DIR_IMAGENES / origen.stem
    if destino.exists() and not forzar:
        existentes = sum(1 for _ in destino.rglob("*") if _.is_file())
        print(f"{destino.name} ya extraido con {existentes} archivos, se omite")
        return destino
    if destino.exists():
        shutil.rmtree(destino)
    destino.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(origen) as comprimido:
        miembros = [m for m in comprimido.infolist() if not m.is_dir()]
        for miembro in tqdm(miembros, desc=f"extrayendo {nombre_zip}", unit="img"):
            nombre_plano = miembro.filename.split("/")[-1]
            if not nombre_plano:
                continue
            with comprimido.open(miembro) as fuente, open(destino / nombre_plano, "wb") as salida:
                shutil.copyfileobj(fuente, salida)
    return destino


def listar_imagenes(particion):
    directorio = DIR_IMAGENES / particion
    if not directorio.exists():
        return []
    return sorted(r for r in directorio.iterdir() if r.suffix.lower() in EXTENSIONES_IMAGEN)


def temporada_desde_nombre(nombre):
    for temporada in CONTEO_OFICIAL_TEMPORADA:
        if nombre.startswith(temporada):
            return temporada
    return "desconocida"


def verificar():
    reporte = {"csv": {}, "imagenes": {}, "temporadas": {}}
    for nombre in ARCHIVOS_ZINDI:
        ruta = DIR_CRUDO / nombre
        reporte["csv"][nombre] = ruta.stat().st_size if ruta.exists() else 0
    for particion in ("train", "test"):
        rutas = listar_imagenes(particion)
        reporte["imagenes"][particion] = len(rutas)
        if particion == "train":
            conteo = {}
            for ruta in rutas:
                clave = temporada_desde_nombre(ruta.name)
                conteo[clave] = conteo.get(clave, 0) + 1
            reporte["temporadas"] = conteo
    return reporte


def imprimir_verificacion(reporte):
    print("Archivos CSV")
    for nombre, tamano in reporte["csv"].items():
        estado = f"{tamano / 1024:.1f} KB" if tamano else "ausente"
        print(f"  {nombre}: {estado}")
    print("Imagenes por particion")
    for particion, cantidad in reporte["imagenes"].items():
        print(f"  {particion}: {cantidad}")
    print("Imagenes de entrenamiento por temporada")
    total_esperado = sum(CONTEO_OFICIAL_TEMPORADA.values())
    for temporada, esperado in CONTEO_OFICIAL_TEMPORADA.items():
        obtenido = reporte["temporadas"].get(temporada, 0)
        marca = "ok" if obtenido == esperado else f"difiere en {obtenido - esperado}"
        print(f"  {temporada}: {obtenido} de {esperado} -> {marca}")
    otras = {k: v for k, v in reporte["temporadas"].items() if k not in CONTEO_OFICIAL_TEMPORADA}
    for temporada, obtenido in otras.items():
        print(f"  {temporada}: {obtenido} sin referencia oficial")
    print(f"  total: {sum(reporte['temporadas'].values())} de {total_esperado}")


def _main():
    analizador = argparse.ArgumentParser(description="Descarga reproducible del dataset")
    analizador.add_argument("accion", choices=("csv", "imagenes", "todo", "verificar"))
    analizador.add_argument("--forzar", action="store_true")
    argumentos = analizador.parse_args()

    if argumentos.accion in ("csv", "todo"):
        descargar_csv(forzar=argumentos.forzar)
    if argumentos.accion in ("imagenes", "todo"):
        descargar_imagenes(forzar=argumentos.forzar)
        for nombre in ARCHIVOS_DRIVE:
            extraer(nombre, forzar=argumentos.forzar)
    imprimir_verificacion(verificar())


if __name__ == "__main__":
    _main()
