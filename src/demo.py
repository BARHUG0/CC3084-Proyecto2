import argparse
import shutil
from pathlib import Path

import uvicorn

from src.api import Almacen, crear_app
from src.config import DIR_DATOS
from src.datos_sinteticos import crear_entorno

DIR_DEMO = DIR_DATOS / "demo"
REGISTROS_DEMO = 600


def _almacen(directorio):
    directorio = Path(directorio)
    return Almacen(
        ruta_conjunto=directorio / "conjunto_modelado.parquet",
        dir_modelos=directorio / "modelos",
        dir_resultados=directorio / "resultados",
        dir_imagenes=directorio / "imagenes",
    )


def almacen_demo(directorio=DIR_DEMO, n_registros=REGISTROS_DEMO, regenerar=False):
    directorio = Path(directorio)
    if regenerar and directorio.exists():
        shutil.rmtree(directorio)
    almacen = _almacen(directorio)
    if not almacen.ruta_conjunto.exists():
        crear_entorno(directorio, n_registros=n_registros, n_campos=max(10, n_registros // 7))
    return almacen


def almacen_vacio(directorio=DIR_DEMO):
    return _almacen(Path(directorio) / "vacio")


def main():
    parser = argparse.ArgumentParser(description="Levanta la API sobre un entorno sintetico de demostracion.")
    parser.add_argument("--puerto", type=int, default=8000)
    parser.add_argument("--registros", type=int, default=REGISTROS_DEMO)
    parser.add_argument("--regenerar", action="store_true", help="Borra y vuelve a crear el entorno de demostracion.")
    parser.add_argument("--vacio", action="store_true", help="Sirve la API sin datos ni modelos.")
    argumentos = parser.parse_args()

    if argumentos.vacio:
        almacen = almacen_vacio()
    else:
        almacen = almacen_demo(n_registros=argumentos.registros, regenerar=argumentos.regenerar)
    print(f"Entorno de demostracion: {almacen.ruta_conjunto.parent}")
    uvicorn.run(crear_app(almacen), host="127.0.0.1", port=argumentos.puerto)


if __name__ == "__main__":
    main()
