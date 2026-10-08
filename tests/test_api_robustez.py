import io

import pandas as pd
import pytest
from fastapi.testclient import TestClient
from PIL import Image
from pydantic import TypeAdapter

from src.api import crear_app
from src.datos_sinteticos import crear_entorno
from src.esquemas import Error, Metricas, ModeloDetalle, Prediccion
from src.evaluacion import guardar_resultados
from src.modelo_base import ModeloMagnitud


@pytest.fixture(scope="session")
def almacen(tmp_path_factory):
    return crear_entorno(tmp_path_factory.mktemp("robustez"))


@pytest.fixture(scope="session")
def cliente(almacen):
    with TestClient(crear_app(almacen)) as cliente:
        yield cliente


@pytest.fixture(scope="session")
def imagen(almacen):
    return next((almacen.dir_imagenes / "train").iterdir())


def validar(respuesta, esquema, estado=200):
    assert respuesta.status_code == estado, respuesta.text
    return TypeAdapter(esquema).validate_python(respuesta.json())


def predecir(cliente, contenido, nombre="imagen.jpg", datos=None, tipo="image/jpeg"):
    return cliente.post("/api/predecir", files={"imagen": (nombre, contenido, tipo)}, data=datos or {})


class ModeloFallido(ModeloMagnitud):
    id = "fallido"
    nombre = "Modelo fallido"
    familia = "referencia"
    descripcion = "Siempre falla al predecir."

    def cargar(self):
        pass

    def predecir(self, imagen, atributos):
        raise RuntimeError("falla deliberada")


def registrar_fallido(cliente, almacen):
    modelo = ModeloFallido(almacen.dir_modelos)
    modelo.ruta_artefacto = almacen.dir_modelos / "constante.joblib"
    cliente.app.state.servicio.registro[modelo.id] = modelo


def test_resultados_corruptos_se_tratan_como_ausentes(cliente, almacen):
    ruta = almacen.dir_resultados / "constante.json"
    original = ruta.read_bytes()
    ruta.write_text("{ no es json", encoding="utf-8")
    try:
        detalle = validar(cliente.get("/api/modelos/constante"), ModeloDetalle)
        assert not detalle.tiene_resultados
    finally:
        ruta.write_bytes(original)
    detalle = validar(cliente.get("/api/modelos/constante"), ModeloDetalle)
    assert detalle.tiene_resultados


def test_imagen_corrupta_en_disco_devuelve_404(cliente, almacen):
    registro = cliente.get("/api/datos/registros", params={"tamano": 1}).json()["registros"][0]
    ruta = almacen.dir_imagenes / "train" / registro["archivo"]
    original = ruta.read_bytes()
    ruta.write_bytes(b"no es una imagen")
    try:
        error = validar(cliente.get(f"/api/datos/registros/{registro['id']}/imagen"), Error, 404)
        assert error.codigo == "imagen_no_disponible"
    finally:
        ruta.write_bytes(original)


def test_imagen_con_demasiados_pixeles_devuelve_413(cliente):
    salida = io.BytesIO()
    Image.new("RGB", (8000, 7000), (60, 140, 50)).save(salida, format="PNG")
    error = validar(predecir(cliente, salida.getvalue(), nombre="grande.png", tipo="image/png"), Error, 413)
    assert error.codigo == "imagen_demasiado_grande"


def test_jpeg_truncado_devuelve_400(cliente, imagen):
    contenido = imagen.read_bytes()
    error = validar(predecir(cliente, contenido[: len(contenido) // 2]), Error, 400)
    assert error.codigo == "imagen_invalida"


def test_modelo_fallido_se_omite_con_advertencia(cliente, almacen, imagen):
    registrar_fallido(cliente, almacen)
    respuesta = validar(predecir(cliente, imagen.read_bytes(), datos={"modelos": ["constante", "fallido"]}), Prediccion)
    assert [p.modelo_id for p in respuesta.predicciones] == ["constante"]
    assert any("fallido" in advertencia for advertencia in respuesta.advertencias)


def test_todos_los_modelos_fallan_devuelve_500(cliente, almacen, imagen):
    registrar_fallido(cliente, almacen)
    error = validar(predecir(cliente, imagen.read_bytes(), datos={"modelos": ["fallido"]}), Error, 500)
    assert error.codigo == "error_modelo"


def test_metricas_omite_alcance_vacio(cliente, almacen):
    prueba = pd.DataFrame(
        {
            "id": ["SIN_DR_1", "SIN_DR_2"],
            "magnitud": [0, 0],
            "temporada": ["LR2020", "LR2020"],
            "etapa": ["S", "S"],
            "dano": ["G", "G"],
        }
    )
    guardar_resultados(
        modelo_id="vacio_dr",
        prueba=prueba,
        predicho=[0.0, 0.0],
        tiempo_entrenamiento_s=0.0,
        tiempo_inferencia_ms=0.0,
        hiperparametros={},
        dir_resultados=almacen.dir_resultados,
    )
    registrar = ModeloFallido(almacen.dir_modelos)
    registrar.ruta_artefacto = almacen.dir_modelos / "constante.joblib"
    registrar.id = "vacio_dr"
    cliente.app.state.servicio.registro["vacio_dr"] = registrar
    respuesta = validar(cliente.get("/api/metricas", params={"modelos": ["vacio_dr"], "alcance": "dr"}), list[Metricas])
    assert respuesta == []
    global_ = validar(cliente.get("/api/metricas", params={"modelos": ["vacio_dr"], "alcance": "global"}), list[Metricas])
    assert global_[0].n == 2


def test_modelos_duplicados_se_eliminan(cliente, imagen):
    metricas = validar(
        cliente.get("/api/metricas", params={"modelos": ["constante", "constante"], "alcance": "dr"}),
        list[Metricas],
    )
    assert len(metricas) == 1
    respuesta = validar(predecir(cliente, imagen.read_bytes(), datos={"modelos": ["constante", "constante"]}), Prediccion)
    assert len(respuesta.predicciones) == 1


def test_modelos_vacio_se_comporta_como_omitido(cliente):
    omitido = validar(cliente.get("/api/metricas"), list[Metricas])
    vacio = validar(cliente.get("/api/metricas", params={"modelos": [""]}), list[Metricas])
    assert [m.modelo_id for m in vacio] == [m.modelo_id for m in omitido]


def test_rango_magnitud_invertido_devuelve_422(cliente):
    error = validar(
        cliente.get("/api/datos/registros", params={"magnitud_min": 50, "magnitud_max": 10}),
        Error,
        422,
    )
    assert error.codigo == "validacion"
