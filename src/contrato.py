import json
import tempfile

from fastapi.testclient import TestClient

from src.api import crear_app
from src.config import RAIZ
from src.datos_sinteticos import crear_entorno

DIR_CONTRATO = RAIZ / "contrato"
RUTA_OPENAPI = DIR_CONTRATO / "openapi.json"
DIR_EJEMPLOS = DIR_CONTRATO / "ejemplos"

PETICIONES = (
    ("salud", "GET", "/api/salud", {}),
    ("catalogos", "GET", "/api/catalogos", {}),
    ("variables", "GET", "/api/datos/variables", {}),
    ("resumen", "GET", "/api/datos/resumen", {}),
    ("registros", "GET", "/api/datos/registros", {"params": {"tamano": 5, "dano": "DR"}}),
    ("distribucion_por_dano", "GET", "/api/datos/distribucion/exceso_verde", {"params": {"por": "dano", "bins": 10}}),
    ("distribucion_magnitud", "GET", "/api/datos/distribucion/magnitud", {"params": {"solo_dr": True}}),
    ("dispersion", "GET", "/api/datos/dispersion", {"params": {"x": "exceso_verde", "muestra": 20}}),
    ("correlaciones", "GET", "/api/datos/correlaciones", {}),
    ("modelos", "GET", "/api/modelos", {}),
    ("modelo_detalle", "GET", "/api/modelos/constante", {}),
    ("metricas", "GET", "/api/metricas", {"params": {"alcance": "dr"}}),
    ("predicciones", "GET", "/api/metricas/constante/predicciones", {"params": {"limite": 10}}),
    ("errores_por_temporada", "GET", "/api/metricas/constante/errores", {"params": {"por": "temporada"}}),
    ("errores_por_magnitud", "GET", "/api/metricas/constante/errores", {"params": {"por": "magnitud"}}),
    ("error_modelo_no_encontrado", "GET", "/api/modelos/inexistente", {}),
    ("error_validacion", "GET", "/api/datos/registros", {"params": {"tamano": 500}}),
)


def documento_openapi():
    return crear_app().openapi()


def _escribir(ruta, contenido):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(contenido, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def exportar():
    _escribir(RUTA_OPENAPI, documento_openapi())
    indice = {}
    with tempfile.TemporaryDirectory() as temporal:
        almacen = crear_entorno(temporal)
        with TestClient(crear_app(almacen)) as cliente:
            for nombre, metodo, ruta, argumentos in PETICIONES:
                respuesta = cliente.request(metodo, ruta, **argumentos)
                _escribir(DIR_EJEMPLOS / f"{nombre}.json", respuesta.json())
                indice[nombre] = {"metodo": metodo, "ruta": ruta, **argumentos, "estado": respuesta.status_code}

            imagen = next((almacen.dir_imagenes / "train").iterdir())
            for nombre, formulario in (
                ("prediccion_dr", {"dano": "DR"}),
                ("prediccion_sin_diagnostico", {}),
                ("prediccion_otro_dano", {"dano": "G"}),
            ):
                with imagen.open("rb") as archivo:
                    respuesta = cliente.post(
                        "/api/predecir",
                        files={"imagen": (imagen.name, archivo, "image/jpeg")},
                        data=formulario,
                    )
                _escribir(DIR_EJEMPLOS / f"{nombre}.json", respuesta.json())
                indice[nombre] = {"metodo": "POST", "ruta": "/api/predecir", "data": formulario, "estado": respuesta.status_code}
    _escribir(DIR_EJEMPLOS / "indice.json", indice)
    return RUTA_OPENAPI


if __name__ == "__main__":
    print(f"Contrato exportado en: {exportar()}")
