import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency, ks_2samp, pearsonr, spearmanr


def resumen_numerico(df, columnas=None):
    if columnas is None:
        columnas = df.select_dtypes(include="number").columns
    filas = []
    for columna in columnas:
        serie = df[columna].dropna()
        if serie.empty:
            continue
        filas.append(
            {
                "variable": columna,
                "conteo": int(serie.count()),
                "faltantes": int(df[columna].isna().sum()),
                "media": serie.mean(),
                "desviacion": serie.std(),
                "minimo": serie.min(),
                "q1": serie.quantile(0.25),
                "mediana": serie.median(),
                "q3": serie.quantile(0.75),
                "maximo": serie.max(),
                "asimetria": serie.skew(),
                "curtosis": serie.kurt(),
            }
        )
    return pd.DataFrame(filas).round(4)


def tabla_frecuencia(df, columna, ordenar_por_frecuencia=False):
    conteo = df[columna].value_counts(dropna=False)
    if not ordenar_por_frecuencia:
        conteo = conteo.sort_index()
    tabla = conteo.rename("frecuencia").reset_index()
    tabla.columns = [columna, "frecuencia"]
    tabla["proporcion"] = tabla["frecuencia"] / tabla["frecuencia"].sum()
    tabla["proporcion_acumulada"] = tabla["proporcion"].cumsum()
    return tabla


def tabla_contingencia(df, fila, columna, normalizar=None):
    mapa = {"fila": "index", "columna": "columns", "total": "all", None: False}
    return pd.crosstab(df[fila], df[columna], normalize=mapa[normalizar], dropna=False)


def resumen_por_grupo(df, grupo, variable):
    agrupado = df.groupby(grupo, observed=False)[variable]
    tabla = agrupado.agg(
        tamano="size",
        media="mean",
        desviacion="std",
        minimo="min",
        q1=lambda s: s.quantile(0.25),
        mediana="median",
        q3=lambda s: s.quantile(0.75),
        maximo="max",
    )
    tabla["prop_cero"] = agrupado.apply(lambda s: (s == 0).mean())
    return tabla.reset_index()


def v_cramer(df, col1, col2):
    tabla = pd.crosstab(df[col1], df[col2])
    if tabla.empty or tabla.shape[0] < 2 or tabla.shape[1] < 2:
        return None
    chi2, _, _, _ = chi2_contingency(tabla, correction=False)
    n = tabla.to_numpy().sum()
    filas, columnas = tabla.shape
    phi2 = chi2 / n
    phi2_corregido = max(0, phi2 - (columnas - 1) * (filas - 1) / (n - 1))
    filas_corregido = filas - (filas - 1) ** 2 / (n - 1)
    columnas_corregido = columnas - (columnas - 1) ** 2 / (n - 1)
    denominador = min(filas_corregido - 1, columnas_corregido - 1)
    if denominador <= 0:
        return None
    return float(np.sqrt(phi2_corregido / denominador))


def matriz_v_cramer(df, columnas):
    matriz = pd.DataFrame(index=columnas, columns=columnas, dtype=float)
    for col1 in columnas:
        for col2 in columnas:
            matriz.loc[col1, col2] = 1.0 if col1 == col2 else v_cramer(df, col1, col2)
    return matriz


def eta_cuadrado(df, categorica, numerica):
    datos = df[[categorica, numerica]].dropna()
    if len(datos) < 2:
        return None
    media_global = datos[numerica].mean()
    ss_total = ((datos[numerica] - media_global) ** 2).sum()
    if ss_total == 0:
        return None
    ss_entre = (
        datos.groupby(categorica, observed=True)[numerica]
        .apply(lambda s: len(s) * (s.mean() - media_global) ** 2)
        .sum()
    )
    return float(ss_entre / ss_total)


def tabla_eta_cuadrado(df, columnas_categoricas, variable_objetivo):
    filas = [
        {"variable": columna, "eta_cuadrado": eta_cuadrado(df, columna, variable_objetivo)}
        for columna in columnas_categoricas
    ]
    return pd.DataFrame(filas).sort_values("eta_cuadrado", ascending=False, ignore_index=True)


def matriz_correlacion(df, columnas, metodo="spearman"):
    return df[columnas].corr(method=metodo)


def correlacion_contra_objetivo(df, columnas_candidatas, objetivo, metodo="spearman"):
    funcion = spearmanr if metodo == "spearman" else pearsonr
    filas = []
    for columna in columnas_candidatas:
        datos = df[[columna, objetivo]].dropna()
        if len(datos) < 3 or datos[columna].nunique() <= 1:
            continue
        coeficiente, valor_p = funcion(datos[columna], datos[objetivo])
        filas.append({"variable": columna, "coeficiente": coeficiente, "valor_p": valor_p})
    tabla = pd.DataFrame(filas)
    if tabla.empty:
        return tabla
    orden = tabla["coeficiente"].abs().sort_values(ascending=False).index
    return tabla.reindex(orden).reset_index(drop=True)


def limites_iqr(serie, factor=1.5):
    q1, q3 = serie.quantile(0.25), serie.quantile(0.75)
    ric = q3 - q1
    return q1 - factor * ric, q3 + factor * ric


def resumen_atipicos(df, columnas, factor=1.5):
    filas = []
    for columna in columnas:
        serie = df[columna].dropna()
        inferior, superior = limites_iqr(serie, factor)
        atipicos = int(((serie < inferior) | (serie > superior)).sum())
        filas.append(
            {
                "variable": columna,
                "limite_inferior": inferior,
                "limite_superior": superior,
                "atipicos": atipicos,
                "proporcion": round(atipicos / len(serie), 4) if len(serie) else 0.0,
            }
        )
    return pd.DataFrame(filas)


def comparar_distribuciones_categoricas(df1, df2, columna, etiquetas=("train", "test")):
    p1 = df1[columna].value_counts(dropna=False, normalize=True)
    p2 = df2[columna].value_counts(dropna=False, normalize=True)
    tabla = pd.concat([p1, p2], axis=1, keys=etiquetas).fillna(0)
    tabla["diferencia"] = tabla[etiquetas[0]] - tabla[etiquetas[1]]
    return tabla.reset_index(names=columna)


def distancia_variacion_total(df1, df2, columna):
    tabla = comparar_distribuciones_categoricas(df1, df2, columna)
    return float(tabla["diferencia"].abs().sum() / 2)


def comparar_variables_numericas(df1, df2, columnas, etiquetas=("train", "test")):
    filas = []
    for columna in columnas:
        s1, s2 = df1[columna].dropna(), df2[columna].dropna()
        if s1.empty or s2.empty:
            continue
        estadistico, valor_p = ks_2samp(s1, s2)
        media1, media2 = s1.mean(), s2.mean()
        diferencia_relativa = (media1 - media2) / media2 if media2 else np.nan
        filas.append(
            {
                "variable": columna,
                f"media_{etiquetas[0]}": media1,
                f"media_{etiquetas[1]}": media2,
                "diferencia_relativa": diferencia_relativa,
                "estadistico_ks": estadistico,
                "valor_p": valor_p,
            }
        )
    return pd.DataFrame(filas).sort_values("estadistico_ks", ascending=False, ignore_index=True)
