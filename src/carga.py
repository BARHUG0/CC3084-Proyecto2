import pandas as pd

from src.config import (
    DIR_CRUDO,
    DIR_IMAGENES,
    DIR_PROCESADO,
    ORDEN_DANOS,
    ORDEN_ETAPAS,
    TEMPORADAS,
)

RENOMBRES = {
    "ID": "id",
    "filename": "archivo",
    "growth_stage": "etapa",
    "damage": "dano",
    "extent": "magnitud",
}

ARCHIVOS_PARTICION = {"train": "Train.csv", "test": "Test.csv"}


def temporada_desde_archivo(nombre):
    for temporada in TEMPORADAS:
        if nombre.startswith(temporada):
            return temporada
    return pd.NA


def id_campo_desde_archivo(nombre):
    if nombre.startswith("L"):
        return nombre[:-9]
    partes = nombre.split("_")
    if "repeat" in nombre:
        return "_".join(partes[:4])
    return "_".join(partes[:3])


def _tipar(df):
    if "etapa" in df:
        df["etapa"] = pd.Categorical(df["etapa"], categories=ORDEN_ETAPAS, ordered=True)
    if "dano" in df:
        df["dano"] = pd.Categorical(df["dano"], categories=ORDEN_DANOS)
    if "magnitud" in df:
        df["magnitud"] = pd.to_numeric(df["magnitud"], errors="coerce")
    df["temporada"] = pd.Categorical(df["temporada"], categories=TEMPORADAS, ordered=True)
    return df


def cargar_particion(particion):
    ruta = DIR_CRUDO / ARCHIVOS_PARTICION[particion]
    if not ruta.exists():
        raise FileNotFoundError(
            f"No se encuentra {ruta}. Ejecute 'python -m src.descarga csv' antes de continuar."
        )
    df = pd.read_csv(ruta)
    df = df.rename(columns={k: v for k, v in RENOMBRES.items() if k in df.columns})
    df["particion"] = particion
    df["temporada"] = df["archivo"].map(temporada_desde_archivo)
    df["id_campo"] = df["archivo"].map(id_campo_desde_archivo)
    df["es_copia"] = df["archivo"].str.contains("Copy", case=True, regex=False)
    df["es_repeticion"] = df["archivo"].str.contains("repeat", case=True, regex=False)
    df["ruta_relativa"] = particion + "/" + df["archivo"]
    df["existe_archivo"] = [
        (DIR_IMAGENES / r).exists() for r in df["ruta_relativa"]
    ]
    return _tipar(df)


def cargar_train():
    return cargar_particion("train")


def cargar_test():
    return cargar_particion("test")


def cargar_metadatos(particion):
    ruta = DIR_PROCESADO / f"metadatos_{particion}.parquet"
    if not ruta.exists():
        raise FileNotFoundError(
            f"No se encuentra {ruta}. Ejecute el notebook 01_adquisicion_datos antes de continuar."
        )
    return pd.read_parquet(ruta)


def guardar_metadatos(df, particion):
    DIR_PROCESADO.mkdir(parents=True, exist_ok=True)
    ruta = DIR_PROCESADO / f"metadatos_{particion}.parquet"
    df.to_parquet(ruta, index=False)
    return ruta


def diccionario_datos(df):
    filas = []
    for columna in df.columns:
        serie = df[columna]
        filas.append(
            {
                "variable": columna,
                "tipo": str(serie.dtype),
                "escala": _escala(serie),
                "no_nulos": int(serie.notna().sum()),
                "nulos": int(serie.isna().sum()),
                "unicos": int(serie.nunique(dropna=True)),
                "ejemplo": serie.dropna().iloc[0] if serie.notna().any() else pd.NA,
            }
        )
    return pd.DataFrame(filas)


def _escala(serie):
    if isinstance(serie.dtype, pd.CategoricalDtype):
        return "ordinal" if serie.dtype.ordered else "nominal"
    if pd.api.types.is_bool_dtype(serie):
        return "binaria"
    if pd.api.types.is_numeric_dtype(serie):
        return "cuantitativa"
    return "texto"
