import pandas as pd

from src.caracteristicas import cargar_cache
from src.carga import cargar_metadatos
from src.config import RUTA_CONJUNTO_MODELADO
from src.esquemas import Atributos
from src.particiones import asignar_subconjunto

ATRIBUTOS = tuple(Atributos.model_fields)

COLUMNAS_CONTEXTO = (
    "id",
    "archivo",
    "ruta_relativa",
    "temporada",
    "etapa",
    "dano",
    "magnitud",
    "id_campo",
    "tipo_captura",
)

VARIABLES = {
    "magnitud": ("Magnitud del dano", "Porcentaje de dano por sequia, de 0 a 100 en pasos de 10.", "numerica", "objetivo"),
    "dano": ("Tipo de dano", "Diagnostico registrado para la fotografia.", "categorica", "contexto"),
    "temporada": ("Temporada", "Temporada agricola de la captura.", "categorica", "contexto"),
    "etapa": ("Etapa de crecimiento", "Etapa fenologica del cultivo.", "categorica", "contexto"),
    "tipo_captura": ("Tipo de captura", "Fotografia inicial, de seguimiento o de reclamo.", "categorica", "contexto"),
    "exceso_verde": ("Exceso de verde", "Indice 2g - r - b promedio sobre la miniatura.", "numerica", "atributo"),
    "saturacion": ("Saturacion", "Saturacion media de los pixeles, de 0 a 1.", "numerica", "atributo"),
    "brillo": ("Brillo", "Luminancia media en escala de 0 a 255.", "numerica", "atributo"),
    "contraste": ("Contraste", "Desviacion estandar de la luminancia.", "numerica", "atributo"),
    "media_r": ("Media del canal rojo", "Intensidad media del canal R.", "numerica", "atributo"),
    "media_g": ("Media del canal verde", "Intensidad media del canal G.", "numerica", "atributo"),
    "media_b": ("Media del canal azul", "Intensidad media del canal B.", "numerica", "atributo"),
    "nitidez": ("Nitidez", "Varianza del laplaciano de la luminancia.", "numerica", "atributo"),
    "megapixeles": ("Megapixeles", "Resolucion de la fotografia original.", "numerica", "atributo"),
    "aspecto": ("Relacion de aspecto", "Ancho dividido entre alto.", "numerica", "atributo"),
    "prop_sobreexpuesta": ("Proporcion sobreexpuesta", "Fraccion de pixeles con luminancia muy alta.", "numerica", "atributo"),
    "prop_subexpuesta": ("Proporcion subexpuesta", "Fraccion de pixeles con luminancia muy baja.", "numerica", "atributo"),
}


def construir_conjunto(guardar=True, ruta=RUTA_CONJUNTO_MODELADO):
    metadatos = cargar_metadatos("train")
    metadatos = metadatos[metadatos["apto_modelado"] & metadatos["dano"].notna()]
    atributos = cargar_cache()
    atributos = atributos.loc[atributos["error"].isna(), ["ruta_relativa", *ATRIBUTOS]]
    conjunto = metadatos[list(COLUMNAS_CONTEXTO)].merge(atributos, on="ruta_relativa", how="inner")
    conjunto["magnitud"] = conjunto["magnitud"].astype(int)
    conjunto = asignar_subconjunto(conjunto.reset_index(drop=True))
    if guardar:
        ruta.parent.mkdir(parents=True, exist_ok=True)
        conjunto.to_parquet(ruta, index=False)
    return conjunto


def cargar_conjunto(ruta=RUTA_CONJUNTO_MODELADO):
    if not ruta.exists():
        raise FileNotFoundError(
            f"No se encuentra {ruta}. Ejecute 'python -m src.conjunto' antes de continuar."
        )
    return pd.read_parquet(ruta)


def _main():
    conjunto = construir_conjunto()
    print(f"Registros: {len(conjunto)}")
    print(conjunto["subconjunto"].value_counts().to_string())
    print(f"Guardado en: {RUTA_CONJUNTO_MODELADO}")


if __name__ == "__main__":
    _main()
