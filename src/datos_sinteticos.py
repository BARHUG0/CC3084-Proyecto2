from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image

from src.api import Almacen
from src.caracteristicas import atributos_imagen
from src.conjunto import ATRIBUTOS
from src.config import DANO_SEQUIA, ORDEN_DANOS, ORDEN_ETAPAS, ORDEN_TIPOS_CAPTURA, SEMILLA, TEMPORADAS
from src.modelos_tabulares import ejecutar_referencia_constante
from src.particiones import asignar_subconjunto

VERDE = np.array([60, 140, 50], dtype=float)
PARDO = np.array([170, 140, 80], dtype=float)


def _imagen(magnitud, rng):
    proporcion = magnitud / 100
    color = (1 - proporcion) * VERDE + proporcion * PARDO
    ruido = rng.normal(0, 18, size=(48, 64, 3))
    return Image.fromarray(np.clip(color + ruido, 0, 255).astype("uint8"))


def crear_entorno(directorio, n_registros=300, n_campos=40):
    directorio = Path(directorio)
    rng = np.random.default_rng(SEMILLA)
    dir_imagenes = directorio / "imagenes"
    (dir_imagenes / "train").mkdir(parents=True, exist_ok=True)
    otros_danos = [d for d in ORDEN_DANOS if d != DANO_SEQUIA]

    filas = []
    for indice in range(n_registros):
        campo = int(rng.integers(1, n_campos + 1))
        es_sequia = rng.random() < 0.35
        dano = DANO_SEQUIA if es_sequia else str(rng.choice(otros_danos))
        magnitud = int(rng.choice(range(10, 101, 10))) if es_sequia else 0
        archivo = f"L{campo}F1C1S1Ip{indice}.jpg"
        ruta_relativa = f"train/{archivo}"
        _imagen(magnitud, rng).save(dir_imagenes / ruta_relativa, format="JPEG")
        with Image.open(dir_imagenes / ruta_relativa) as imagen:
            atributos = atributos_imagen(imagen)
        filas.append(
            {
                "id": f"ID_SINT{indice:04d}",
                "archivo": archivo,
                "ruta_relativa": ruta_relativa,
                "temporada": str(rng.choice(TEMPORADAS)),
                "etapa": None if rng.random() < 0.1 else str(rng.choice(ORDEN_ETAPAS)),
                "dano": dano,
                "magnitud": magnitud,
                "id_campo": f"L{campo}F1",
                "tipo_captura": str(rng.choice(ORDEN_TIPOS_CAPTURA)),
                **{nombre: atributos[nombre] for nombre in ATRIBUTOS},
            }
        )

    conjunto = asignar_subconjunto(pd.DataFrame(filas))
    almacen = Almacen(
        ruta_conjunto=directorio / "conjunto_modelado.parquet",
        dir_modelos=directorio / "modelos",
        dir_resultados=directorio / "resultados",
        dir_imagenes=dir_imagenes,
    )
    conjunto.to_parquet(almacen.ruta_conjunto, index=False)
    ejecutar_referencia_constante(conjunto, almacen.dir_modelos, almacen.dir_resultados)
    return almacen
