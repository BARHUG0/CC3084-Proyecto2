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
    "magnitud": ("Magnitud del daño", "Porcentaje de daño por sequía, de 0 a 100 en pasos de 10.", "numerica", "objetivo"),
    "dano": ("Tipo de daño", "Diagnóstico registrado para la fotografía.", "categorica", "contexto"),
    "temporada": ("Temporada", "Temporada agrícola de la captura.", "categorica", "contexto"),
    "etapa": ("Etapa de crecimiento", "Etapa fenológica del cultivo.", "categorica", "contexto"),
    "tipo_captura": ("Tipo de captura", "Fotografía inicial, de seguimiento o de reclamo.", "categorica", "contexto"),
    "exceso_verde": ("Exceso de verde", "Índice 2g - r - b promedio sobre la miniatura.", "numerica", "atributo"),
    "saturacion": ("Saturación", "Saturación media de los píxeles, de 0 a 1.", "numerica", "atributo"),
    "brillo": ("Brillo", "Luminancia media en escala de 0 a 255.", "numerica", "atributo"),
    "contraste": ("Contraste", "Desviación estándar de la luminancia.", "numerica", "atributo"),
    "media_r": ("Media del canal rojo", "Intensidad media del canal R.", "numerica", "atributo"),
    "media_g": ("Media del canal verde", "Intensidad media del canal G.", "numerica", "atributo"),
    "media_b": ("Media del canal azul", "Intensidad media del canal B.", "numerica", "atributo"),
    "nitidez": ("Nitidez", "Varianza del laplaciano de la luminancia.", "numerica", "atributo"),
    "megapixeles": ("Megapíxeles", "Resolución de la fotografía original.", "numerica", "atributo"),
    "aspecto": ("Relación de aspecto", "Ancho dividido entre alto.", "numerica", "atributo"),
    "prop_sobreexpuesta": ("Proporción sobreexpuesta", "Fracción de píxeles con luminancia muy alta.", "numerica", "atributo"),
    "prop_subexpuesta": ("Proporción subexpuesta", "Fracción de píxeles con luminancia muy baja.", "numerica", "atributo"),
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
