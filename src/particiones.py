from sklearn.model_selection import GroupKFold, GroupShuffleSplit

from src.config import DANO_SEQUIA, PROPORCION_PRUEBA, SEMILLA, TEMPORADA_PRUEBA_TEMPORAL

COLUMNA_GRUPO = "id_campo"


def asignar_subconjunto(df, proporcion_prueba=PROPORCION_PRUEBA, semilla=SEMILLA):
    divisor = GroupShuffleSplit(n_splits=1, test_size=proporcion_prueba, random_state=semilla)
    _, indices_prueba = next(divisor.split(df, groups=df[COLUMNA_GRUPO]))
    resultado = df.copy()
    resultado["subconjunto"] = "entrenamiento"
    resultado.iloc[indices_prueba, resultado.columns.get_loc("subconjunto")] = "prueba"
    return resultado


def entrenamiento_y_prueba(conjunto, solo_dr=False):
    datos = conjunto[conjunto["dano"] == DANO_SEQUIA] if solo_dr else conjunto
    entrenamiento = datos[datos["subconjunto"] == "entrenamiento"].reset_index(drop=True)
    prueba = datos[datos["subconjunto"] == "prueba"].reset_index(drop=True)
    return entrenamiento, prueba


def pliegues_por_campo(entrenamiento, n_pliegues=5):
    return list(GroupKFold(n_splits=n_pliegues).split(entrenamiento, groups=entrenamiento[COLUMNA_GRUPO]))


def separar_por_temporada(conjunto, temporada=TEMPORADA_PRUEBA_TEMPORAL):
    es_prueba = conjunto["temporada"] == temporada
    return (
        conjunto[~es_prueba].reset_index(drop=True),
        conjunto[es_prueba].reset_index(drop=True),
    )


def campos_compartidos(a, b):
    return sorted(set(a[COLUMNA_GRUPO]) & set(b[COLUMNA_GRUPO]))
