from fastapi.testclient import TestClient

from src.api import crear_app
from src.demo import almacen_demo, almacen_vacio


def salud(almacen):
    with TestClient(crear_app(almacen)) as cliente:
        return cliente.get("/api/salud").json()


def test_almacen_demo_crea_entorno_con_datos_y_modelo(tmp_path):
    almacen = almacen_demo(tmp_path, n_registros=80)
    assert almacen.ruta_conjunto.exists()
    respuesta = salud(almacen)
    assert respuesta["datos_disponibles"]
    assert "constante" in respuesta["modelos_disponibles"]
    assert "constante" in respuesta["modelos_con_resultados"]


def test_almacen_demo_reutiliza_entorno_existente(tmp_path):
    ruta = almacen_demo(tmp_path, n_registros=80).ruta_conjunto
    modificado = ruta.stat().st_mtime_ns
    almacen_demo(tmp_path, n_registros=80)
    assert ruta.stat().st_mtime_ns == modificado


def test_almacen_demo_regenera_entorno(tmp_path):
    almacen = almacen_demo(tmp_path, n_registros=80)
    marca = almacen.dir_resultados / "sobrante.json"
    marca.write_text("{}")
    almacen_demo(tmp_path, n_registros=80, regenerar=True)
    assert not marca.exists()
    assert almacen.ruta_conjunto.exists()


def test_almacen_vacio_no_tiene_datos_ni_modelos(tmp_path):
    respuesta = salud(almacen_vacio(tmp_path))
    assert not respuesta["datos_disponibles"]
    assert respuesta["modelos_disponibles"] == []
    assert respuesta["modelos_con_resultados"] == []
