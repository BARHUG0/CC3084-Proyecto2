import pandas as pd

from src.config import DIR_IMAGENES, EXTENSIONES_IMAGEN, ORDEN_DANOS, ORDEN_ETAPAS

PASO_MAGNITUD = 10
MAGNITUD_MINIMA = 0
MAGNITUD_MAXIMA = 100


def resumen_faltantes(df):
    total = len(df)
    filas = []
    for columna in df.columns:
        nulos = int(df[columna].isna().sum())
        filas.append(
            {
                "variable": columna,
                "faltantes": nulos,
                "porcentaje": round(100 * nulos / total, 3) if total else 0.0,
            }
        )
    return pd.DataFrame(filas).sort_values("faltantes", ascending=False, ignore_index=True)


def duplicados_registro(df):
    filas = []
    for columna in ("id", "archivo"):
        if columna not in df:
            continue
        marcados = df[columna].duplicated(keep=False)
        filas.append(
            {
                "variable": columna,
                "registros_duplicados": int(marcados.sum()),
                "valores_afectados": int(df.loc[marcados, columna].nunique()),
            }
        )
    return pd.DataFrame(filas)


def validar_dominios(df):
    filas = []
    if "etapa" in df:
        filas.append(
            {
                "variable": "etapa",
                "regla": f"valor en {list(ORDEN_ETAPAS)}",
                "violaciones": int(df["etapa"].isna().sum()),
            }
        )
    if "dano" in df:
        filas.append(
            {
                "variable": "dano",
                "regla": f"valor en {list(ORDEN_DANOS)}",
                "violaciones": int(df["dano"].isna().sum()),
            }
        )
    if "magnitud" in df:
        serie = df["magnitud"]
        fuera_rango = serie.lt(MAGNITUD_MINIMA) | serie.gt(MAGNITUD_MAXIMA)
        no_multiplo = serie.notna() & serie.mod(PASO_MAGNITUD).ne(0)
        filas.append(
            {
                "variable": "magnitud",
                "regla": f"rango {MAGNITUD_MINIMA} a {MAGNITUD_MAXIMA}",
                "violaciones": int(fuera_rango.sum()),
            }
        )
        filas.append(
            {
                "variable": "magnitud",
                "regla": f"multiplo de {PASO_MAGNITUD}",
                "violaciones": int(no_multiplo.sum()),
            }
        )
    return pd.DataFrame(filas)


def regla_estructural(df):
    columnas = ["caso", "registros", "porcentaje"]
    if "dano" not in df or "magnitud" not in df:
        return pd.DataFrame(columns=columnas)
    total = len(df)
    magnitud_positiva_no_sequia = df["magnitud"].gt(0) & df["dano"].ne("DR")
    sequia_sin_magnitud = df["dano"].eq("DR") & df["magnitud"].eq(0)
    sano_con_magnitud = df["dano"].eq("G") & df["magnitud"].gt(0)
    casos = [
        ("magnitud positiva con dano distinto de sequia", magnitud_positiva_no_sequia),
        ("sequia declarada con magnitud cero", sequia_sin_magnitud),
        ("crecimiento sano con magnitud positiva", sano_con_magnitud),
    ]
    return pd.DataFrame(
        [
            {
                "caso": nombre,
                "registros": int(mascara.sum()),
                "porcentaje": round(100 * int(mascara.sum()) / total, 3) if total else 0.0,
            }
            for nombre, mascara in casos
        ],
        columns=columnas,
    )


def imagenes_huerfanas(df, particion):
    directorio = DIR_IMAGENES / particion
    if not directorio.exists():
        return pd.Index([])
    en_disco = {r.name for r in directorio.iterdir() if r.suffix.lower() in EXTENSIONES_IMAGEN}
    return pd.Index(sorted(en_disco - set(df["archivo"])))


def registros_sin_imagen(df):
    return df.loc[~df["existe_archivo"], "archivo"]


def marcar_calidad(df):
    resultado = df.copy()
    resultado["magnitud_valida"] = True
    if "magnitud" in resultado:
        serie = resultado["magnitud"]
        resultado["magnitud_valida"] = (
            serie.notna()
            & serie.between(MAGNITUD_MINIMA, MAGNITUD_MAXIMA)
            & serie.mod(PASO_MAGNITUD).eq(0)
        )
    resultado["etiqueta_coherente"] = True
    if "dano" in resultado and "magnitud" in resultado:
        magnitud_positiva_no_sequia = resultado["magnitud"].gt(0) & resultado["dano"].ne("DR")
        sequia_sin_magnitud = resultado["dano"].eq("DR") & resultado["magnitud"].eq(0)
        resultado["etiqueta_coherente"] = ~(magnitud_positiva_no_sequia | sequia_sin_magnitud)
    resultado["apto_modelado"] = (
        resultado["existe_archivo"]
        & ~resultado["es_copia"]
        & resultado["magnitud_valida"]
        & resultado["temporada"].notna()
        & resultado["id_campo"].notna()
    )
    return resultado


def bitacora(df, particion):
    total = len(df)
    registros = [
        ("registros leidos", total, "sin accion"),
        (
            "valores faltantes en variables clave",
            int(df[[c for c in ("etapa", "dano", "magnitud") if c in df]].isna().sum().sum()),
            "no se imputa, se conserva el faltante y se documenta",
        ),
        (
            "identificadores duplicados",
            int(df["id"].duplicated().sum()) if "id" in df else 0,
            "se revisa el origen antes de eliminar",
        ),
        (
            "formato de nombre desconocido",
            int(df["formato_nombre"].eq("desconocido").sum()) if "formato_nombre" in df else 0,
            "se revisa el patron antes de derivar variables adicionales",
        ),
        (
            "tipo de captura no identificado",
            int(df["tipo_captura"].isna().sum()) if "tipo_captura" in df else 0,
            "se conservan y se excluyen de los cruces que usen esta variable",
        ),
        (
            "registros sin imagen en disco",
            int((~df["existe_archivo"]).sum()),
            "se excluyen del modelado",
        ),
        (
            "imagenes en disco sin registro",
            len(imagenes_huerfanas(df, particion)),
            "se excluyen del analisis tabular",
        ),
        (
            "temporada no identificada",
            int(df["temporada"].isna().sum()),
            "se revisa el patron del nombre de archivo",
        ),
        (
            "campos unicos identificados",
            int(df["id_campo"].nunique()),
            "definen los grupos de particion",
        ),
    ]
    if "magnitud" in df:
        marcado = marcar_calidad(df)
        registros.append(
            (
                "magnitud fuera de dominio",
                int((~marcado["magnitud_valida"]).sum()),
                "se excluyen del modelado",
            )
        )
        registros.append(
            (
                "etiqueta incoherente con la magnitud",
                int((~marcado["etiqueta_coherente"]).sum()),
                "se conservan y se analizan como ruido de etiquetado",
            )
        )
        estructural = regla_estructural(df)
        conteos = dict(zip(estructural["caso"], estructural["registros"]))
        total_roto = conteos.get(
            "magnitud positiva con dano distinto de sequia", 0
        ) + conteos.get("sequia declarada con magnitud cero", 0)
        registros.append(
            (
                "registros que rompen la regla estructural dano-magnitud",
                total_roto,
                "se conservan y se analizan como ruido de etiquetado",
            )
        )
    return pd.DataFrame(registros, columns=["verificacion", "registros", "decision"])
