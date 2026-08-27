import re

import pandas as pd

from src.config import (
    DIR_CRUDO,
    DIR_IMAGENES,
    DIR_PROCESADO,
    ORDEN_DANOS,
    ORDEN_ETAPAS,
    ORDEN_TIPOS_CAPTURA,
    TEMPORADAS,
)

RENOMBRES = {
    "ID": "id",
    "filename": "archivo",
    "growth_stage": "etapa",
    "damage": "dano",
    "extent": "magnitud",
    "season": "temporada",
}

ARCHIVOS_PARTICION = {"train": "Train.csv", "test": "Test.csv"}

RE_CODIFICADO = re.compile(
    r"^L(?P<productor>\d+)F(?P<campo>\d+)C(?P<cultivo>\d+)S(?P<sitio>\d+)"
    r"(?P<tipo>Ip|Rp|Dp)(?P<secuencia>\d+)\.jpg$",
    re.IGNORECASE,
)
RE_SECUENCIAL = re.compile(
    r"^(?P<productor>[^_]+)_(?P<tipo>initial|repeat)_(?P<n>\d+)_(?P<resto>.+)\.JPG$",
    re.IGNORECASE,
)
MAPA_TIPO_CODIFICADO = {"ip": "inicial", "rp": "seguimiento", "dp": "reclamo"}
MAPA_TIPO_SECUENCIAL = {"initial": "inicial", "repeat": "seguimiento"}


def descomponer_nombre_archivo(nombre):
    coincidencia = RE_CODIFICADO.match(nombre)
    if coincidencia:
        productor = f"L{coincidencia.group('productor')}"
        campo = f"F{coincidencia.group('campo')}"
        return {
            "formato_nombre": "codificado",
            "id_productor": productor,
            "id_campo": f"{productor}{campo}",
            "codigo_cultivo": f"C{coincidencia.group('cultivo')}",
            "id_sitio": f"S{coincidencia.group('sitio')}",
            "tipo_captura": MAPA_TIPO_CODIFICADO[coincidencia.group("tipo").lower()],
        }
    coincidencia = RE_SECUENCIAL.match(nombre)
    if coincidencia:
        id_productor = f"U{coincidencia.group('productor')}"
        return {
            "formato_nombre": "secuencial",
            "id_productor": id_productor,
            "id_campo": id_productor,
            "codigo_cultivo": pd.NA,
            "id_sitio": pd.NA,
            "tipo_captura": MAPA_TIPO_SECUENCIAL[coincidencia.group("tipo").lower()],
        }
    return {
        "formato_nombre": "desconocido",
        "id_productor": pd.NA,
        "id_campo": pd.NA,
        "codigo_cultivo": pd.NA,
        "id_sitio": pd.NA,
        "tipo_captura": pd.NA,
    }


def _tipar(df):
    if "etapa" in df:
        df["etapa"] = pd.Categorical(df["etapa"], categories=ORDEN_ETAPAS, ordered=True)
    if "dano" in df:
        df["dano"] = pd.Categorical(df["dano"], categories=ORDEN_DANOS)
    if "magnitud" in df:
        df["magnitud"] = pd.to_numeric(df["magnitud"], errors="coerce")
    df["temporada"] = pd.Categorical(df["temporada"], categories=TEMPORADAS, ordered=True)
    if "tipo_captura" in df:
        df["tipo_captura"] = pd.Categorical(
            df["tipo_captura"], categories=ORDEN_TIPOS_CAPTURA, ordered=True
        )
    if "formato_nombre" in df:
        df["formato_nombre"] = pd.Categorical(df["formato_nombre"])
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
    descomposicion = pd.DataFrame(
        [descomponer_nombre_archivo(nombre) for nombre in df["archivo"]], index=df.index
    )
    df = pd.concat([df, descomposicion], axis=1)
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
