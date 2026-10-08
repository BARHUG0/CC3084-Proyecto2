import json

import pytest
from fastapi.testclient import TestClient
from pydantic import TypeAdapter

from src.api import Almacen, crear_app
from src.contrato import RUTA_OPENAPI, documento_openapi
from src.datos_sinteticos import crear_entorno
from src.esquemas import (
    Catalogos,
    Correlacion,
    Dispersion,
    Distribucion,
    Error,
    ErrorGrupo,
    Metricas,
    ModeloDetalle,
    ModeloInfo,
    PaginaRegistros,
    Prediccion,
    PuntoPrediccion,
    ResumenDatos,
    Salud,
    Variable,
)
from src.registro_modelos import crear_registro


@pytest.fixture(scope="session")
def almacen(tmp_path_factory):
    return crear_entorno(tmp_path_factory.mktemp("entorno"))


@pytest.fixture(scope="session")
def cliente(almacen):
    with TestClient(crear_app(almacen)) as cliente:
        yield cliente


@pytest.fixture(scope="session")
def cliente_vacio(tmp_path_factory):
    vacio = tmp_path_factory.mktemp("vacio")
    almacen = Almacen(vacio / "conjunto.parquet", vacio / "modelos", vacio / "resultados", vacio / "imagenes")
    with TestClient(crear_app(almacen)) as cliente:
        yield cliente


@pytest.fixture(scope="session")
def imagen(almacen):
    return next((almacen.dir_imagenes / "train").iterdir())


def validar(respuesta, esquema, estado=200):
    assert respuesta.status_code == estado, respuesta.text
    return TypeAdapter(esquema).validate_python(respuesta.json())


def predecir(cliente, imagen, datos=None, tipo="image/jpeg"):
    with imagen.open("rb") as archivo:
        return cliente.post("/api/predecir", files={"imagen": (imagen.name, archivo, tipo)}, data=datos or {})


def test_openapi_exportado_coincide_con_la_api():
    assert RUTA_OPENAPI.exists(), "Ejecute 'python -m src.contrato'."
    assert json.loads(RUTA_OPENAPI.read_text(encoding="utf-8")) == documento_openapi(), (
        "El contrato cambio. Ejecute 'python -m src.contrato' y confirme el nuevo openapi.json."
    )


def test_todo_modelo_registrado_cumple_la_interfaz():
    for modelo_id, modelo in crear_registro().items():
        assert modelo_id and modelo.nombre and modelo.descripcion
        assert modelo.familia in ("referencia", "tabular", "cnn")
        assert isinstance(modelo.entradas, tuple)


def test_salud(cliente):
    salud = validar(cliente.get("/api/salud"), Salud)
    assert salud.datos_disponibles
    assert "constante" in salud.modelos_disponibles


def test_catalogos(cliente):
    catalogos = validar(cliente.get("/api/catalogos"), Catalogos)
    assert [d.codigo for d in catalogos.danos][1] == "DR"


def test_variables(cliente):
    variables = validar(cliente.get("/api/datos/variables"), list[Variable])
    assert {"magnitud", "exceso_verde"} <= {v.nombre for v in variables}


def test_resumen(cliente):
    resumen = validar(cliente.get("/api/datos/resumen"), ResumenDatos)
    assert sum(c.conteo for c in resumen.por_subconjunto) == resumen.total_registros
    assert [c.clave for c in resumen.magnitud_global] == [str(v) for v in range(0, 101, 10)]


def test_registros_filtrados_y_paginados(cliente):
    pagina = validar(cliente.get("/api/datos/registros", params={"dano": "DR", "tamano": 7, "orden": "magnitud", "descendente": True}), PaginaRegistros)
    assert len(pagina.registros) <= 7
    assert all(r.dano == "DR" for r in pagina.registros)
    magnitudes = [r.magnitud for r in pagina.registros]
    assert magnitudes == sorted(magnitudes, reverse=True)
    lejana = validar(cliente.get("/api/datos/registros", params={"pagina": 999}), PaginaRegistros)
    assert lejana.registros == []


def test_imagen_de_registro(cliente):
    registro = cliente.get("/api/datos/registros", params={"tamano": 1}).json()["registros"][0]
    respuesta = cliente.get(f"/api/datos/registros/{registro['id']}/imagen", params={"lado": 64})
    assert respuesta.status_code == 200
    assert respuesta.headers["content-type"] == "image/jpeg"
    validar(cliente.get("/api/datos/registros/NO_EXISTE/imagen"), Error, 404)


@pytest.mark.parametrize("variable, por", [("exceso_verde", "dano"), ("magnitud", "ninguno"), ("brillo", "temporada")])
def test_distribucion(cliente, variable, por):
    distribucion = validar(cliente.get(f"/api/datos/distribucion/{variable}", params={"por": por}), Distribucion)
    assert all(len(g.conteos) == len(distribucion.bordes) - 1 for g in distribucion.grupos)


def test_dispersion_y_correlaciones(cliente):
    dispersion = validar(cliente.get("/api/datos/dispersion", params={"muestra": 10}), Dispersion)
    assert len(dispersion.puntos) <= 10
    validar(cliente.get("/api/datos/correlaciones"), list[Correlacion])


def test_modelos(cliente):
    modelos = validar(cliente.get("/api/modelos"), list[ModeloInfo])
    assert any(m.id == "constante" and m.disponible and m.tiene_resultados for m in modelos)
    validar(cliente.get("/api/modelos/constante"), ModeloDetalle)
    assert validar(cliente.get("/api/modelos/inexistente"), Error, 404).codigo == "modelo_no_encontrado"


@pytest.mark.parametrize("alcance", ["global", "dr"])
def test_metricas(cliente, alcance):
    metricas = validar(cliente.get("/api/metricas", params={"alcance": alcance, "modelos": ["constante"]}), list[Metricas])
    assert metricas[0].alcance == alcance and metricas[0].n > 0


def test_predicciones_y_errores(cliente):
    puntos = validar(cliente.get("/api/metricas/constante/predicciones", params={"limite": 5}), list[PuntoPrediccion])
    assert len(puntos) <= 5 and all(p.dano == "DR" for p in puntos)
    for por in ("temporada", "etapa", "magnitud"):
        validar(cliente.get("/api/metricas/constante/errores", params={"por": por}), list[ErrorGrupo])


def test_prediccion_segun_diagnostico(cliente, imagen):
    con_dr = validar(predecir(cliente, imagen, {"dano": "DR"}), Prediccion)
    assert not con_dr.predicciones[0].regla_aplicada and con_dr.advertencias == []
    otro = validar(predecir(cliente, imagen, {"dano": "G"}), Prediccion)
    assert otro.predicciones[0].magnitud == 0 and otro.predicciones[0].regla_aplicada
    sin = validar(predecir(cliente, imagen, {"dano": ""}), Prediccion)
    assert sin.dano_considerado is None and sin.advertencias


def test_errores_de_prediccion(cliente, imagen):
    assert validar(predecir(cliente, imagen, tipo="text/plain"), Error, 415).codigo == "formato_no_soportado"
    assert validar(predecir(cliente, imagen, {"modelos": ["inexistente"]}), Error, 404).codigo == "modelo_no_encontrado"
    assert validar(predecir(cliente, imagen, {"dano": "XX"}), Error, 422).codigo == "validacion"
    respuesta = cliente.post("/api/predecir", files={"imagen": ("a.jpg", b"no es imagen", "image/jpeg")})
    assert validar(respuesta, Error, 400).codigo == "imagen_invalida"


def test_api_sin_datos_ni_modelos(cliente_vacio, imagen):
    salud = validar(cliente_vacio.get("/api/salud"), Salud)
    assert not salud.datos_disponibles and salud.modelos_disponibles == []
    assert validar(cliente_vacio.get("/api/datos/resumen"), Error, 503).codigo == "datos_no_disponibles"
    assert validar(cliente_vacio.get("/api/metricas"), list[Metricas]) == []
    assert validar(cliente_vacio.get("/api/metricas/constante/errores"), Error, 409).codigo == "sin_resultados"
    assert validar(predecir(cliente_vacio, imagen), Error, 409).codigo == "sin_modelos_disponibles"
