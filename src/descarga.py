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


