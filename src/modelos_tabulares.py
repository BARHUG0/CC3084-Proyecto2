import time

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import RandomizedSearchCV

from src.config import DANO_SEQUIA, DIR_MODELOS, DIR_RESULTADOS, SEMILLA
from src.evaluacion import completar_con_regla, guardar_resultados
from src.modelo_base import ModeloMagnitud
from src.particiones import entrenamiento_y_prueba, pliegues_por_campo

ATRIBUTOS_BOSQUE = (
    "exceso_verde",
    "saturacion",
    "brillo",
    "contraste",
    "media_r",
    "media_g",
    "media_b",
    "prop_sobreexpuesta",
    "prop_subexpuesta",
)

ESPACIO_BOSQUE = {
    "n_estimators": [100, 200, 300, 500],
    "max_depth": [None, 5, 10, 20],
    "min_samples_leaf": [1, 2, 5, 10, 20, 50],
    "max_features": ["sqrt", 0.5, 1.0],
}

# se refitea con rmse; el mae solo alimenta el historial
METRICAS_AJUSTE = {"rmse": "neg_root_mean_squared_error", "mae": "neg_mean_absolute_error"}


def _nativo(valor):
    return valor.item() if isinstance(valor, np.generic) else valor


class PredictorConstante(ModeloMagnitud):
    id = "constante"
    nombre = "Predictor constante"
    familia = "referencia"
    descripcion = "Predice la magnitud media de los registros DR de entrenamiento."
    entradas = ()

    def __init__(self, dir_modelos=DIR_MODELOS):
        super().__init__(dir_modelos)
        self.valor = None

    def entrenar(self, entrenamiento):
        self.valor = float(entrenamiento["magnitud"].mean())
        return self

    def guardar(self):
        self.ruta_artefacto.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({"valor": self.valor}, self.ruta_artefacto)

    def cargar(self):
        self.valor = float(joblib.load(self.ruta_artefacto)["valor"])

    def predecir(self, imagen, atributos):
        return self.valor

    def predecir_lote(self, df):
        return np.full(len(df), self.valor, dtype=float)


class ModeloSklearn(ModeloMagnitud):
    def __init__(self, dir_modelos=DIR_MODELOS):
        super().__init__(dir_modelos)
        self.estimador = None

    def _matriz(self, df):
        return df[list(self.entradas)].astype(float)

    def entrenar(self, entrenamiento, estimador):
        self.estimador = estimador.fit(self._matriz(entrenamiento), entrenamiento["magnitud"])
        return self

    def guardar(self):
        self.ruta_artefacto.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({"estimador": self.estimador, "entradas": list(self.entradas)}, self.ruta_artefacto)

    def cargar(self):
        # solo se cargan artefactos que genera el propio proyecto, nunca algo subido por un usuario
        artefacto = joblib.load(self.ruta_artefacto)
        self.estimador = artefacto["estimador"]
        self.entradas = tuple(artefacto["entradas"])

    def predecir(self, imagen, atributos):
        fila = pd.DataFrame([{nombre: atributos.get(nombre) for nombre in self.entradas}], dtype=float)
        return float(self.estimador.predict(fila)[0])

    def predecir_lote(self, df):
        return self.estimador.predict(self._matriz(df))


class RegresionExcesoVerde(ModeloSklearn):
    id = "regresion_exceso_verde"
    nombre = "Regresion lineal sobre exceso de verde"
    familia = "referencia"
    descripcion = "Ajusta una recta entre el exceso de verde de la fotografia y la magnitud DR."
    entradas = ("exceso_verde",)
    extension = ".joblib"


class RandomForestMagnitud(ModeloSklearn):
    id = "random_forest"
    nombre = "Random Forest"
    familia = "tabular"
    descripcion = "Bosque aleatorio de regresion sobre atributos globales de color y exposicion."
    entradas = ATRIBUTOS_BOSQUE
    extension = ".joblib"

    def importancias(self):
        pares = zip(self.entradas, self.estimador.feature_importances_)
        return [
            {"variable": variable, "importancia": float(valor)}
            for variable, valor in sorted(pares, key=lambda par: par[1], reverse=True)
        ]


def ajustar_bosque(entrenamiento, entradas=ATRIBUTOS_BOSQUE, n_iter=30):
    busqueda = RandomizedSearchCV(
        RandomForestRegressor(random_state=SEMILLA),
        ESPACIO_BOSQUE,
        n_iter=n_iter,
        scoring=METRICAS_AJUSTE,
        refit="rmse",
        cv=pliegues_por_campo(entrenamiento),
        random_state=SEMILLA,
        n_jobs=-1,
    )
    return busqueda.fit(entrenamiento[list(entradas)].astype(float), entrenamiento["magnitud"])


def historial_busqueda(busqueda):
    resultados = busqueda.cv_results_
    return [
        {
            "parametros": {clave: _nativo(valor) for clave, valor in parametros.items()},
            "rmse_validacion": float(-resultados["mean_test_rmse"][indice]),
            "mae_validacion": float(-resultados["mean_test_mae"][indice]),
            "elegido": bool(indice == busqueda.best_index_),
        }
        for indice, parametros in enumerate(resultados["params"])
    ]


def _guardar_y_evaluar(modelo, conjunto, tiempo_entrenamiento_s, hiperparametros, dir_resultados, **extras):
    modelo.guardar()
    _, prueba_dr = entrenamiento_y_prueba(conjunto, solo_dr=True)
    _, prueba = entrenamiento_y_prueba(conjunto)
    inicio = time.perf_counter()
    predicho_dr = modelo.predecir_lote(prueba_dr)
    tiempo_inferencia_ms = 1000 * (time.perf_counter() - inicio) / max(1, len(prueba_dr))

    return guardar_resultados(
        modelo_id=modelo.id,
        prueba=prueba,
        predicho=completar_con_regla(prueba, predicho_dr),
        tiempo_entrenamiento_s=tiempo_entrenamiento_s,
        tiempo_inferencia_ms=tiempo_inferencia_ms,
        hiperparametros=hiperparametros,
        dir_resultados=dir_resultados,
        **extras,
    )


def ejecutar_referencia_constante(conjunto, dir_modelos=DIR_MODELOS, dir_resultados=DIR_RESULTADOS):
    entrenamiento, _ = entrenamiento_y_prueba(conjunto, solo_dr=True)
    modelo = PredictorConstante(dir_modelos)

    inicio = time.perf_counter()
    modelo.entrenar(entrenamiento)
    tiempo_entrenamiento_s = time.perf_counter() - inicio

    return _guardar_y_evaluar(
        modelo,
        conjunto,
        tiempo_entrenamiento_s,
        {"valor": round(modelo.valor, 4), "subconjunto": DANO_SEQUIA},
        dir_resultados,
    )


def ejecutar_regresion_exceso_verde(conjunto, dir_modelos=DIR_MODELOS, dir_resultados=DIR_RESULTADOS):
    entrenamiento, _ = entrenamiento_y_prueba(conjunto, solo_dr=True)
    modelo = RegresionExcesoVerde(dir_modelos)

    inicio = time.perf_counter()
    modelo.entrenar(entrenamiento, LinearRegression())
    tiempo_entrenamiento_s = time.perf_counter() - inicio

    return _guardar_y_evaluar(
        modelo,
        conjunto,
        tiempo_entrenamiento_s,
        {
            "pendiente": round(float(modelo.estimador.coef_[0]), 4),
            "intercepto": round(float(modelo.estimador.intercept_), 4),
        },
        dir_resultados,
    )


def ejecutar_random_forest(conjunto, dir_modelos=DIR_MODELOS, dir_resultados=DIR_RESULTADOS, n_iter=30):
    entrenamiento, _ = entrenamiento_y_prueba(conjunto, solo_dr=True)
    modelo = RandomForestMagnitud(dir_modelos)

    # el tiempo incluye la busqueda completa y el reajuste final
    inicio = time.perf_counter()
    busqueda = ajustar_bosque(entrenamiento, modelo.entradas, n_iter)
    tiempo_entrenamiento_s = time.perf_counter() - inicio
    modelo.estimador = busqueda.best_estimator_

    return _guardar_y_evaluar(
        modelo,
        conjunto,
        tiempo_entrenamiento_s,
        {clave: _nativo(valor) for clave, valor in busqueda.best_params_.items()},
        dir_resultados,
        historial_ajuste=historial_busqueda(busqueda),
        importancias=modelo.importancias(),
    )
