import json

import numpy as np
import pandas as pd

from src.config import DANO_SEQUIA, DIR_RESULTADOS
from src.esquemas import ResultadosModelo


def metricas(real, predicho):
    real = np.asarray(real, dtype=float)
    predicho = np.asarray(predicho, dtype=float)
    error = predicho - real
    n = int(real.size)
    if n == 0:
        return {"n": 0, "mae": 0.0, "rmse": 0.0, "r2": None}
    suma_total = float(((real - real.mean()) ** 2).sum())
    r2 = 1 - float((error**2).sum()) / suma_total if n > 1 and suma_total > 0 else None
    return {
        "n": n,
        "mae": float(np.abs(error).mean()),
        "rmse": float(np.sqrt((error**2).mean())),
        "r2": r2,
    }


def metricas_por_grupo(df, columna, real="real", predicho="predicho"):
    filas = []
    for grupo, subconjunto in df.groupby(columna, observed=True, sort=True):
        valores = metricas(subconjunto[real], subconjunto[predicho])
        filas.append({"grupo": grupo, "n": valores["n"], "mae": valores["mae"], "rmse": valores["rmse"]})
    return pd.DataFrame(filas, columns=["grupo", "n", "mae", "rmse"])


def completar_con_regla(prueba, predicho_dr):
    es_sequia = (prueba["dano"] == DANO_SEQUIA).to_numpy()
    predicho_dr = np.asarray(predicho_dr, dtype=float)
    if predicho_dr.size != es_sequia.sum():
        raise ValueError(
            f"Se esperaban {int(es_sequia.sum())} predicciones DR y se recibieron {predicho_dr.size}."
        )
    completo = np.zeros(len(prueba), dtype=float)
    completo[es_sequia] = predicho_dr
    return completo


def _opcional(valor):
    return None if pd.isna(valor) else str(valor)


def guardar_resultados(
    modelo_id,
    prueba,
    predicho,
    tiempo_entrenamiento_s,
    tiempo_inferencia_ms,
    hiperparametros,
    historial_ajuste=(),
    curva_entrenamiento=(),
    importancias=(),
    dir_resultados=DIR_RESULTADOS,
):
    predicho = np.clip(np.asarray(predicho, dtype=float), 0, 100)
    if predicho.size != len(prueba):
        raise ValueError("Debe existir una prediccion por cada registro de prueba.")
    resultados = ResultadosModelo(
        modelo_id=modelo_id,
        tiempo_entrenamiento_s=float(tiempo_entrenamiento_s),
        tiempo_inferencia_ms=float(tiempo_inferencia_ms),
        hiperparametros=hiperparametros,
        predicciones=[
            {
                "id": str(fila.id),
                "real": float(fila.magnitud),
                "predicho": float(valor),
                "temporada": str(fila.temporada),
                "etapa": _opcional(fila.etapa),
                "dano": str(fila.dano),
            }
            for fila, valor in zip(prueba.itertuples(index=False), predicho)
        ],
        historial_ajuste=list(historial_ajuste),
        curva_entrenamiento=list(curva_entrenamiento),
        importancias=list(importancias),
    )
    dir_resultados.mkdir(parents=True, exist_ok=True)
    ruta = dir_resultados / f"{modelo_id}.json"
    ruta.write_text(resultados.model_dump_json(indent=2), encoding="utf-8")
    return ruta


def cargar_resultados(modelo_id, dir_resultados=DIR_RESULTADOS):
    ruta = dir_resultados / f"{modelo_id}.json"
    if not ruta.exists():
        return None
    return ResultadosModelo.model_validate(json.loads(ruta.read_text(encoding="utf-8")))


def tabla_predicciones(resultados):
    tabla = pd.DataFrame([p.model_dump() for p in resultados.predicciones])
    tabla["etapa"] = tabla["etapa"].astype("object").where(tabla["etapa"].notna(), None)
    return tabla
