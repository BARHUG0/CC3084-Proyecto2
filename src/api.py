import io
import json
import math
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Annotated, Literal

import numpy as np
import pandas as pd
from fastapi import APIRouter, FastAPI, File, Form, Path as Ruta, Query, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from PIL import Image, ImageFile, UnidentifiedImageError
from pydantic import ValidationError
from scipy.stats import spearmanr
from starlette.exceptions import HTTPException

from src.caracteristicas import atributos_imagen
from src.config import (
    DANO_SEQUIA,
    DIR_IMAGENES,
    DIR_MODELOS,
    DIR_RESULTADOS,
    ETAPAS_CRECIMIENTO,
    ORDEN_DANOS,
    ORDEN_ETAPAS,
    ORDEN_TIPOS_CAPTURA,
    PALETA,
    RUTA_CONJUNTO_MODELADO,
    SECUENCIA_COLORES,
    TEMPORADAS,
    TIPOS_CAPTURA,
    TIPOS_DANO,
)
from src.conjunto import ATRIBUTOS, VARIABLES
from src.esquemas import (
    AgrupacionDatos,
    AgrupacionError,
    Alcance,
    Atributos,
    CampoOrden,
    Catalogos,
    Conteo,
    Correlacion,
    Dano,
    Dispersion,
    Distribucion,
    Error,
    ErrorGrupo,
    Etapa,
    GrupoDistribucion,
    Metricas,
    ModeloDetalle,
    ModeloInfo,
    PaginaRegistros,
    Prediccion,
    PrediccionModelo,
    PuntoDispersion,
    PuntoPrediccion,
    Registro,
    ResumenDatos,
    Salud,
    Subconjunto,
    Temporada,
    Variable,
    VariableNumerica,
)
from src.evaluacion import cargar_resultados, metricas, metricas_por_grupo, tabla_predicciones
from src.registro_modelos import crear_registro

VERSION = "1.0.0"
PREFIJO = "/api"
ORIGENES_PERMITIDOS = ("http://localhost:5173", "http://127.0.0.1:5173")
TIPOS_IMAGEN = ("image/jpeg", "image/png")
TAMANO_MAXIMO_IMAGEN = 15 * 1024 * 1024
PIXELES_MAXIMOS_IMAGEN = 50 * 1000 * 1000
SEMILLA_MUESTRA = 42
BORDES_MAGNITUD = [float(b) for b in np.arange(-5, 106, 10)]
ADVERTENCIA_SIN_DIAGNOSTICO = "Sin diagnostico: se asume sequia (DR) y se estima su severidad."
ADVERTENCIA_OTRO_DANO = "Diagnostico distinto de DR: la magnitud se fija en 0 por la regla del conjunto."

ETIQUETAS = {
    "dano": TIPOS_DANO,
    "etapa": ETAPAS_CRECIMIENTO,
    "temporada": {t: t for t in TEMPORADAS},
    "subconjunto": {"entrenamiento": "Entrenamiento", "prueba": "Prueba"},
}
ORDENES = {
    "dano": ORDEN_DANOS,
    "etapa": ORDEN_ETAPAS,
    "temporada": TEMPORADAS,
    "subconjunto": ("entrenamiento", "prueba"),
}


@dataclass
class Almacen:
    ruta_conjunto: Path = RUTA_CONJUNTO_MODELADO
    dir_modelos: Path = DIR_MODELOS
    dir_resultados: Path = DIR_RESULTADOS
    dir_imagenes: Path = DIR_IMAGENES


class ErrorApi(Exception):
    def __init__(self, estado, codigo, detalle):
        self.estado, self.codigo, self.detalle = estado, codigo, detalle


def _errores(*estados, validacion=True):
    respuestas = {estado: {"model": Error} for estado in estados}
    if validacion:
        respuestas[422] = {"model": Error}
    return respuestas


def _cargar_estricto(imagen):
    anterior = ImageFile.LOAD_TRUNCATED_IMAGES
    ImageFile.LOAD_TRUNCATED_IMAGES = False
    try:
        imagen.load()
    finally:
        ImageFile.LOAD_TRUNCATED_IMAGES = anterior


@dataclass
class Servicio:
    almacen: Almacen
    registro: dict = field(init=False)
    _conjunto: pd.DataFrame | None = field(default=None, init=False)
    _marca_conjunto: float | None = field(default=None, init=False)
    _resultados: dict = field(default_factory=dict, init=False)

    def __post_init__(self):
        self.registro = crear_registro(self.almacen.dir_modelos)

    def datos_disponibles(self):
        return self.almacen.ruta_conjunto.exists()

    def conjunto(self):
        ruta = self.almacen.ruta_conjunto
        if not ruta.exists():
            raise ErrorApi(503, "datos_no_disponibles", "No existe el conjunto de modelado. Ejecute 'python -m src.conjunto'.")
        marca = ruta.stat().st_mtime
        if self._conjunto is None or marca != self._marca_conjunto:
            conjunto = pd.read_parquet(ruta)
            for columna in ("temporada", "etapa", "dano", "tipo_captura", "subconjunto"):
                conjunto[columna] = conjunto[columna].astype("object").where(conjunto[columna].notna(), None)
            self._conjunto, self._marca_conjunto = conjunto, marca
        return self._conjunto

    def modelo(self, modelo_id):
        if modelo_id not in self.registro:
            raise ErrorApi(404, "modelo_no_encontrado", f"No existe el modelo '{modelo_id}'.")
        return self.registro[modelo_id]

    def resultados(self, modelo_id):
        ruta = self.almacen.dir_resultados / f"{modelo_id}.json"
        if not ruta.exists():
            return None
        marca = ruta.stat().st_mtime
        guardado = self._resultados.get(modelo_id)
        if guardado is None or guardado[0] != marca:
            try:
                resultados = cargar_resultados(modelo_id, self.almacen.dir_resultados)
            except (json.JSONDecodeError, ValidationError):
                resultados = None
            guardado = (marca, None if resultados is None else (resultados, tabla_predicciones(resultados)))
            self._resultados[modelo_id] = guardado
        return guardado[1]

    def resultados_obligatorios(self, modelo_id):
        self.modelo(modelo_id)
        encontrados = self.resultados(modelo_id)
        if encontrados is None:
            raise ErrorApi(409, "sin_resultados", f"El modelo '{modelo_id}' aun no tiene resultados de prueba.")
        return encontrados

    def info_modelo(self, modelo, detalle=False):
        encontrados = self.resultados(modelo.id)
        resultados = encontrados[0] if encontrados else None
        datos = {
            "id": modelo.id,
            "nombre": modelo.nombre,
            "familia": modelo.familia,
            "descripcion": modelo.descripcion,
            "entradas": list(modelo.entradas),
            "hiperparametros": resultados.hiperparametros if resultados else {},
            "disponible": modelo.disponible,
            "tiene_resultados": resultados is not None,
        }
        if not detalle:
            return ModeloInfo(**datos)
        return ModeloDetalle(
            **datos,
            historial_ajuste=resultados.historial_ajuste if resultados else [],
            curva_entrenamiento=resultados.curva_entrenamiento if resultados else [],
            importancias=resultados.importancias if resultados else [],
        )


def _filtrar_alcance(tabla, alcance):
    return tabla[tabla["dano"] == DANO_SEQUIA] if alcance == "dr" else tabla


def _filtrar_dr(conjunto, solo_dr):
    return conjunto[conjunto["dano"] == DANO_SEQUIA] if solo_dr else conjunto


def _conteos(serie, columna):
    frecuencias = serie.value_counts()
    return [
        Conteo(clave=clave, etiqueta=ETIQUETAS[columna].get(clave, clave), conteo=int(frecuencias.get(clave, 0)))
        for clave in ORDENES[columna]
    ]


def _conteos_magnitud(serie):
    frecuencias = serie.astype(int).value_counts()
    return [
        Conteo(clave=str(valor), etiqueta=f"{valor} %", conteo=int(frecuencias.get(valor, 0)))
        for valor in range(0, 101, 10)
    ]


def _flotante(valor):
    if valor is None or pd.isna(valor):
        return None
    return float(valor)


def _atributos(fila):
    return Atributos(**{nombre: _flotante(fila.get(nombre)) for nombre in ATRIBUTOS})


def _registro(fila):
    return Registro(
        id=fila["id"],
        archivo=fila["archivo"],
        temporada=fila["temporada"],
        etapa=fila["etapa"],
        dano=fila["dano"],
        magnitud=int(fila["magnitud"]),
        subconjunto=fila["subconjunto"],
        tipo_captura=fila["tipo_captura"],
        atributos=_atributos(fila),
    )


def _magnitud_redondeada(valor):
    return int(min(100, max(0, math.floor(valor / 10 + 0.5) * 10)))


def crear_app(almacen=None):
    servicio = Servicio(almacen or Almacen())
    app = FastAPI(
        title="CGIAR Eyes on the Ground - API de magnitud de dano por sequia",
        version=VERSION,
        description=(
            "Contrato entre los modelos entrenados y el frontend. Todas las respuestas de error "
            "usan el esquema Error con un codigo estable. La magnitud se expresa de 0 a 100."
        ),
        generate_unique_id_function=lambda ruta: ruta.name,
    )
    app.state.servicio = servicio
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(ORIGENES_PERMITIDOS),
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    @app.exception_handler(ErrorApi)
    async def manejar_error_api(_: Request, error: ErrorApi):
        return JSONResponse(status_code=error.estado, content={"detalle": error.detalle, "codigo": error.codigo})

    @app.exception_handler(HTTPException)
    async def manejar_error_http(_: Request, error: HTTPException):
        return JSONResponse(status_code=error.status_code, content={"detalle": str(error.detail), "codigo": f"http_{error.status_code}"})

    @app.exception_handler(RequestValidationError)
    async def manejar_error_validacion(_: Request, error: RequestValidationError):
        mensajes = [f"{'.'.join(str(p) for p in e['loc'])}: {e['msg']}" for e in error.errors()]
        return JSONResponse(status_code=422, content={"detalle": "; ".join(mensajes), "codigo": "validacion"})

    sistema = APIRouter(prefix=PREFIJO, tags=["sistema"])
    datos = APIRouter(prefix=f"{PREFIJO}/datos", tags=["datos"])
    modelos = APIRouter(prefix=f"{PREFIJO}/modelos", tags=["modelos"])
    rendimiento = APIRouter(prefix=f"{PREFIJO}/metricas", tags=["metricas"])
    prediccion = APIRouter(prefix=PREFIJO, tags=["prediccion"])

    @sistema.get("/salud", response_model=Salud)
    def obtener_salud():
        return Salud(
            estado="ok",
            version=VERSION,
            datos_disponibles=servicio.datos_disponibles(),
            modelos_disponibles=[m.id for m in servicio.registro.values() if m.disponible],
            modelos_con_resultados=[m.id for m in servicio.registro.values() if servicio.resultados(m.id)],
        )

    @sistema.get("/catalogos", response_model=Catalogos)
    def obtener_catalogos():
        def opciones(orden, nombres):
            return [{"codigo": codigo, "nombre": nombres.get(codigo, codigo)} for codigo in orden]

        return Catalogos(
            temporadas=opciones(TEMPORADAS, {}),
            danos=opciones(ORDEN_DANOS, TIPOS_DANO),
            etapas=opciones(ORDEN_ETAPAS, ETAPAS_CRECIMIENTO),
            tipos_captura=opciones(ORDEN_TIPOS_CAPTURA, TIPOS_CAPTURA),
            paleta=PALETA,
            secuencia_colores=list(SECUENCIA_COLORES),
        )

    @datos.get("/variables", response_model=list[Variable])
    def listar_variables():
        return [
            Variable(
                nombre=nombre,
                etiqueta=etiqueta,
                descripcion=descripcion,
                tipo=tipo,
                rol=rol,
                usada_en_modelos=[m.id for m in servicio.registro.values() if nombre in m.entradas],
            )
            for nombre, (etiqueta, descripcion, tipo, rol) in VARIABLES.items()
        ]

    @datos.get("/resumen", response_model=ResumenDatos, responses=_errores(503, validacion=False))
    def obtener_resumen():
        conjunto = servicio.conjunto()
        sequia = conjunto[conjunto["dano"] == DANO_SEQUIA]
        return ResumenDatos(
            total_registros=len(conjunto),
            registros_dr=len(sequia),
            campos=int(conjunto["id_campo"].nunique()),
            por_subconjunto=_conteos(conjunto["subconjunto"], "subconjunto"),
            por_temporada=_conteos(conjunto["temporada"], "temporada"),
            por_dano=_conteos(conjunto["dano"], "dano"),
            por_etapa=_conteos(conjunto["etapa"], "etapa"),
            magnitud_global=_conteos_magnitud(conjunto["magnitud"]),
            magnitud_dr=_conteos_magnitud(sequia["magnitud"]),
        )

    @datos.get("/registros", response_model=PaginaRegistros, responses=_errores(503))
    def listar_registros(
        pagina: Annotated[int, Query(ge=1)] = 1,
        tamano: Annotated[int, Query(ge=1, le=100)] = 25,
        temporada: Temporada | None = None,
        dano: Dano | None = None,
        etapa: Etapa | None = None,
        subconjunto: Subconjunto | None = None,
        magnitud_min: Annotated[int | None, Query(ge=0, le=100)] = None,
        magnitud_max: Annotated[int | None, Query(ge=0, le=100)] = None,
        orden: CampoOrden = "id",
        descendente: bool = False,
    ):
        if magnitud_min is not None and magnitud_max is not None and magnitud_min > magnitud_max:
            raise ErrorApi(422, "validacion", "magnitud_min no puede ser mayor que magnitud_max.")
        tabla = servicio.conjunto()
        for columna, valor in (("temporada", temporada), ("dano", dano), ("etapa", etapa), ("subconjunto", subconjunto)):
            if valor is not None:
                tabla = tabla[tabla[columna] == valor]
        if magnitud_min is not None:
            tabla = tabla[tabla["magnitud"] >= magnitud_min]
        if magnitud_max is not None:
            tabla = tabla[tabla["magnitud"] <= magnitud_max]
        tabla = tabla.sort_values([orden, "id"], ascending=not descendente, na_position="last", kind="stable")
        total = len(tabla)
        inicio = (pagina - 1) * tamano
        return PaginaRegistros(
            total=total,
            pagina=pagina,
            tamano=tamano,
            paginas=math.ceil(total / tamano),
            registros=[_registro(fila) for _, fila in tabla.iloc[inicio : inicio + tamano].iterrows()],
        )

    @datos.get("/registros/{registro_id}/imagen", responses={200: {"content": {"image/jpeg": {}}}, **_errores(404, 503)}, response_class=Response)
    def obtener_imagen(
        registro_id: str,
        lado: Annotated[int, Query(ge=64, le=1024)] = 256,
    ):
        conjunto = servicio.conjunto()
        filas = conjunto[conjunto["id"] == registro_id]
        if filas.empty:
            raise ErrorApi(404, "registro_no_encontrado", f"No existe el registro '{registro_id}'.")
        ruta = servicio.almacen.dir_imagenes / filas.iloc[0]["ruta_relativa"]
        if not ruta.exists():
            raise ErrorApi(404, "imagen_no_disponible", "La imagen no esta descargada en el servidor.")
        try:
            with Image.open(ruta) as imagen:
                miniatura = imagen.convert("RGB")
                miniatura.thumbnail((lado, lado))
        except (UnidentifiedImageError, OSError):
            raise ErrorApi(404, "imagen_no_disponible", "La imagen no esta descargada en el servidor.")
        salida = io.BytesIO()
        miniatura.save(salida, format="JPEG", quality=85)
        return Response(content=salida.getvalue(), media_type="image/jpeg")

    @datos.get("/distribucion/{variable}", response_model=Distribucion, responses=_errores(503))
    def obtener_distribucion(
        variable: Annotated[VariableNumerica, Ruta()],
        por: AgrupacionDatos = "ninguno",
        bins: Annotated[int, Query(ge=5, le=50)] = 20,
        solo_dr: bool = False,
    ):
        tabla = _filtrar_dr(servicio.conjunto(), solo_dr)
        valores = tabla[variable].dropna().astype(float)
        if variable == "magnitud":
            bordes = BORDES_MAGNITUD
        elif valores.empty:
            bordes = [0.0, 1.0]
        else:
            bordes = [float(b) for b in np.histogram_bin_edges(valores, bins=bins)]
        if por == "ninguno":
            grupos = [("todos", "Todos", valores)]
        else:
            grupos = [
                (clave, ETIQUETAS[por].get(clave, clave), tabla.loc[tabla[por] == clave, variable].dropna().astype(float))
                for clave in ORDENES[por]
                if (tabla[por] == clave).any()
            ]
        return Distribucion(
            variable=variable,
            por=por,
            bordes=bordes,
            grupos=[
                GrupoDistribucion(grupo=clave, etiqueta=etiqueta, conteos=np.histogram(serie, bins=bordes)[0].astype(int).tolist())
                for clave, etiqueta, serie in grupos
            ],
        )

    @datos.get("/dispersion", response_model=Dispersion, responses=_errores(503))
    def obtener_dispersion(
        x: VariableNumerica = "exceso_verde",
        y: VariableNumerica = "magnitud",
        solo_dr: bool = True,
        muestra: Annotated[int, Query(ge=1, le=5000)] = 1000,
    ):
        tabla = _filtrar_dr(servicio.conjunto(), solo_dr)
        tabla = tabla.dropna(subset=[x, y])
        total = len(tabla)
        if total > muestra:
            tabla = tabla.sample(n=muestra, random_state=SEMILLA_MUESTRA)
        return Dispersion(
            x=x,
            y=y,
            total_disponible=total,
            puntos=[
                PuntoDispersion(id=f["id"], x=float(f[x]), y=float(f[y]), dano=f["dano"], temporada=f["temporada"])
                for _, f in tabla.iterrows()
            ],
        )

    @datos.get("/correlaciones", response_model=list[Correlacion], responses=_errores(503))
    def listar_correlaciones(solo_dr: bool = True):
        tabla = _filtrar_dr(servicio.conjunto(), solo_dr)
        resultado = []
        for variable in ATRIBUTOS:
            pares = tabla[[variable, "magnitud"]].dropna()
            coeficiente = None
            if len(pares) > 2 and pares[variable].nunique() > 1 and pares["magnitud"].nunique() > 1:
                coeficiente = float(spearmanr(pares[variable], pares["magnitud"]).statistic)
            resultado.append(Correlacion(variable=variable, spearman=coeficiente, n=len(pares)))
        return resultado

    @modelos.get("", response_model=list[ModeloInfo])
    def listar_modelos():
        return [servicio.info_modelo(m) for m in servicio.registro.values()]

    @modelos.get("/{modelo_id}", response_model=ModeloDetalle, responses=_errores(404, validacion=False))
    def obtener_modelo(modelo_id: str):
        return servicio.info_modelo(servicio.modelo(modelo_id), detalle=True)

    @rendimiento.get("", response_model=list[Metricas], responses=_errores(404))
    def listar_metricas(
        modelos: Annotated[list[str] | None, Query(description="Repita el parametro para varios modelos. Si se omite, se usan todos los que tienen resultados.")] = None,
        alcance: Alcance = "dr",
    ):
        identificadores = list(dict.fromkeys(m for m in modelos if m)) if modelos else []
        if not identificadores:
            identificadores = list(servicio.registro)
        for modelo_id in identificadores:
            servicio.modelo(modelo_id)
        respuesta = []
        for modelo_id in identificadores:
            encontrados = servicio.resultados(modelo_id)
            if encontrados is None:
                continue
            resultados, tabla = encontrados
            tabla = _filtrar_alcance(tabla, alcance)
            if tabla.empty:
                continue
            valores = metricas(tabla["real"], tabla["predicho"])
            respuesta.append(
                Metricas(
                    modelo_id=modelo_id,
                    alcance=alcance,
                    tiempo_entrenamiento_s=resultados.tiempo_entrenamiento_s,
                    tiempo_inferencia_ms=resultados.tiempo_inferencia_ms,
                    **valores,
                )
            )
        return respuesta

    @rendimiento.get("/{modelo_id}/predicciones", response_model=list[PuntoPrediccion], responses=_errores(404, 409))
    def listar_predicciones(
        modelo_id: str,
        alcance: Alcance = "dr",
        limite: Annotated[int | None, Query(ge=1, le=20000)] = None,
    ):
        _, tabla = servicio.resultados_obligatorios(modelo_id)
        tabla = _filtrar_alcance(tabla, alcance)
        if limite is not None and len(tabla) > limite:
            tabla = tabla.sample(n=limite, random_state=SEMILLA_MUESTRA)
        return [
            PuntoPrediccion(
                id=f["id"],
                real=f["real"],
                predicho=f["predicho"],
                error=f["predicho"] - f["real"],
                temporada=f["temporada"],
                etapa=f["etapa"],
                dano=f["dano"],
            )
            for f in tabla.to_dict("records")
        ]

    @rendimiento.get("/{modelo_id}/errores", response_model=list[ErrorGrupo], responses=_errores(404, 409))
    def listar_errores(modelo_id: str, por: AgrupacionError = "temporada", alcance: Alcance = "dr"):
        _, tabla = servicio.resultados_obligatorios(modelo_id)
        tabla = _filtrar_alcance(tabla, alcance).copy()
        if por == "magnitud":
            tabla["magnitud"] = tabla["real"].astype(int)
            orden = list(range(0, 101, 10))
            etiquetas = {valor: f"{valor} %" for valor in orden}
        else:
            orden = list(ORDENES[por])
            etiquetas = ETIQUETAS[por]
        agrupado = metricas_por_grupo(tabla.dropna(subset=[por]), por).set_index("grupo")
        return [
            ErrorGrupo(
                grupo=str(clave),
                etiqueta=etiquetas.get(clave, str(clave)),
                n=int(agrupado.at[clave, "n"]),
                mae=float(agrupado.at[clave, "mae"]),
                rmse=float(agrupado.at[clave, "rmse"]),
            )
            for clave in orden
            if clave in agrupado.index
        ]

    @prediccion.post("/predecir", response_model=Prediccion, responses=_errores(400, 404, 409, 413, 415, 500))
    async def predecir(
        imagen: Annotated[UploadFile, File(description="Fotografia JPEG o PNG del cultivo.")],
        dano: Annotated[Dano | Literal[""] | None, Form(description="Diagnostico conocido. Omitir o enviar vacio si no se conoce.")] = None,
        modelos: Annotated[list[str] | None, Form(description="Repita el campo para varios modelos. Si se omite, se usan todos los disponibles.")] = None,
    ):
        if imagen.content_type not in TIPOS_IMAGEN:
            raise ErrorApi(415, "formato_no_soportado", "La imagen debe ser JPEG o PNG.")
        contenido = await imagen.read()
        if len(contenido) > TAMANO_MAXIMO_IMAGEN:
            raise ErrorApi(413, "imagen_demasiado_grande", "La imagen supera el limite de 15 MB.")
        try:
            with Image.open(io.BytesIO(contenido)) as original:
                _cargar_estricto(original)
                if original.width * original.height > PIXELES_MAXIMOS_IMAGEN:
                    raise ErrorApi(413, "imagen_demasiado_grande", "La imagen supera el limite de 50 megapixeles.")
                atributos = Atributos(**{k: v for k, v in atributos_imagen(original).items() if k in ATRIBUTOS})
                rgb = original.convert("RGB")
        except (UnidentifiedImageError, OSError):
            raise ErrorApi(400, "imagen_invalida", "No fue posible leer la imagen.")

        dano = dano or None
        if modelos:
            identificadores = list(dict.fromkeys(m for m in modelos if m))
        else:
            identificadores = []
        if identificadores:
            seleccion = [servicio.modelo(modelo_id) for modelo_id in identificadores]
            no_disponibles = [m.id for m in seleccion if not m.disponible]
            if no_disponibles:
                raise ErrorApi(409, "modelo_no_disponible", f"Modelos sin artefacto entrenado: {', '.join(no_disponibles)}.")
        else:
            seleccion = [m for m in servicio.registro.values() if m.disponible]
            if not seleccion:
                raise ErrorApi(409, "sin_modelos_disponibles", "Ningun modelo tiene artefacto entrenado.")

        valores = atributos.model_dump()
        predicciones = []
        advertencias = []
        fallos = []
        for modelo in seleccion:
            try:
                modelo.asegurar_carga()
                inicio = time.perf_counter()
                magnitud, regla = modelo.estimar(rgb, valores, dano)
                tiempo_ms = round(1000 * (time.perf_counter() - inicio), 3)
            except Exception as error:
                fallos.append(f"'{modelo.id}': {type(error).__name__}: {error}")
                advertencias.append(f"El modelo '{modelo.id}' fallo y se omitio.")
                continue
            magnitud = round(magnitud, 2)
            predicciones.append(
                PrediccionModelo(
                    modelo_id=modelo.id,
                    nombre=modelo.nombre,
                    magnitud=magnitud,
                    magnitud_redondeada=_magnitud_redondeada(magnitud),
                    regla_aplicada=regla,
                    tiempo_ms=tiempo_ms,
                )
            )
        if not predicciones:
            raise ErrorApi(500, "error_modelo", f"Todos los modelos fallaron: {'; '.join(fallos)}")
        if dano is None:
            advertencias.append(ADVERTENCIA_SIN_DIAGNOSTICO)
        elif dano != DANO_SEQUIA:
            advertencias.append(ADVERTENCIA_OTRO_DANO)
        return Prediccion(dano_considerado=dano, atributos=atributos, predicciones=predicciones, advertencias=advertencias)

    for enrutador in (sistema, datos, modelos, rendimiento, prediccion):
        app.include_router(enrutador)
    return app


app = crear_app()
