import pandas as pd
import pytest

from src.datos_sinteticos import crear_entorno
from src.evaluacion import cargar_resultados
from src.modelos_tabulares import ESPACIO_BOSQUE, ejecutar_random_forest, ejecutar_regresion_exceso_verde
from src.registro_modelos import crear_registro


@pytest.fixture(scope="module")
def entorno(tmp_path_factory):
    almacen = crear_entorno(tmp_path_factory.mktemp("tabulares"))
    return almacen, pd.read_parquet(almacen.ruta_conjunto)


def comprobar_modelo(almacen, conjunto, modelo_id):
    resultados = cargar_resultados(modelo_id, almacen.dir_resultados)
    assert len(resultados.predicciones) == (conjunto["subconjunto"] == "prueba").sum()
    assert all(0 <= p.predicho <= 100 for p in resultados.predicciones)

    modelo = crear_registro(almacen.dir_modelos)[modelo_id]
    assert modelo.disponible
    atributos = conjunto.iloc[0].to_dict()
    magnitud, regla = modelo.estimar(None, atributos, "DR")
    assert 0 <= magnitud <= 100 and not regla
    assert modelo.estimar(None, atributos, "G") == (0.0, True)
    return resultados


def test_regresion_exceso_verde_entrena_guarda_y_predice(entorno):
    almacen, conjunto = entorno
    ejecutar_regresion_exceso_verde(conjunto, almacen.dir_modelos, almacen.dir_resultados)

    resultados = comprobar_modelo(almacen, conjunto, "regresion_exceso_verde")
    assert set(resultados.hiperparametros) == {"pendiente", "intercepto"}


def test_random_forest_entrena_guarda_y_predice(entorno):
    almacen, conjunto = entorno
    ejecutar_random_forest(conjunto, almacen.dir_modelos, almacen.dir_resultados, n_iter=2)

    resultados = comprobar_modelo(almacen, conjunto, "random_forest")
    assert len(resultados.historial_ajuste) == 2
    assert sum(paso.elegido for paso in resultados.historial_ajuste) == 1
    assert all(paso.mae_validacion is not None for paso in resultados.historial_ajuste)
    assert all(resultados.hiperparametros[clave] in valores for clave, valores in ESPACIO_BOSQUE.items())

    modelo = crear_registro(almacen.dir_modelos)["random_forest"]
    assert {i.variable for i in resultados.importancias} == set(modelo.entradas)
