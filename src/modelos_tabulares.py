import time

import joblib
import numpy as np

from src.config import DANO_SEQUIA, DIR_MODELOS, DIR_RESULTADOS
from src.evaluacion import completar_con_regla, guardar_resultados
from src.modelo_base import ModeloMagnitud
from src.particiones import entrenamiento_y_prueba


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


def ejecutar_referencia_constante(conjunto, dir_modelos=DIR_MODELOS, dir_resultados=DIR_RESULTADOS):
    entrenamiento, prueba = entrenamiento_y_prueba(conjunto, solo_dr=True)
    modelo = PredictorConstante(dir_modelos)

    inicio = time.perf_counter()
    modelo.entrenar(entrenamiento)
    tiempo_entrenamiento_s = time.perf_counter() - inicio
    modelo.guardar()

    _, prueba_completa = entrenamiento_y_prueba(conjunto)
    inicio = time.perf_counter()
    predicho_dr = modelo.predecir_lote(prueba)
    tiempo_inferencia_ms = 1000 * (time.perf_counter() - inicio) / max(1, len(prueba))

    return guardar_resultados(
        modelo_id=modelo.id,
        prueba=prueba_completa,
        predicho=completar_con_regla(prueba_completa, predicho_dr),
        tiempo_entrenamiento_s=tiempo_entrenamiento_s,
        tiempo_inferencia_ms=tiempo_inferencia_ms,
        hiperparametros={"valor": round(modelo.valor, 4), "subconjunto": DANO_SEQUIA},
        dir_resultados=dir_resultados,
    )
