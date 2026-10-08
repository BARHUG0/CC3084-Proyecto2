from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Temporada = Literal["LR2020", "SR2020", "LR2021", "SR2021"]
Dano = Literal["G", "DR", "DS", "FD", "ND", "PS", "WD", "WN"]
Etapa = Literal["S", "V", "F", "M"]
TipoCaptura = Literal["inicial", "seguimiento", "reclamo"]
Subconjunto = Literal["entrenamiento", "prueba"]
Familia = Literal["referencia", "tabular", "cnn"]
Alcance = Literal["global", "dr"]
AgrupacionDatos = Literal["ninguno", "dano", "temporada", "etapa"]
AgrupacionError = Literal["temporada", "etapa", "magnitud"]
TipoVariable = Literal["numerica", "categorica"]
RolVariable = Literal["objetivo", "atributo", "contexto"]
ValorHiperparametro = str | int | float | bool | None
VariableNumerica = Literal[
    "magnitud",
    "exceso_verde",
    "saturacion",
    "brillo",
    "contraste",
    "media_r",
    "media_g",
    "media_b",
    "nitidez",
    "megapixeles",
    "aspecto",
    "prop_sobreexpuesta",
    "prop_subexpuesta",
]
CampoOrden = Literal["id", "temporada", "etapa", "dano", "magnitud", "exceso_verde", "brillo", "saturacion", "contraste"]


class Esquema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Error(Esquema):
    detalle: str = Field(description="Mensaje legible para mostrar al usuario.")
    codigo: str = Field(description="Identificador estable del error para el frontend.")


class Salud(Esquema):
    estado: Literal["ok"]
    version: str
    datos_disponibles: bool
    modelos_disponibles: list[str]
    modelos_con_resultados: list[str]


class Opcion(Esquema):
    codigo: str
    nombre: str


class Catalogos(Esquema):
    temporadas: list[Opcion]
    danos: list[Opcion]
    etapas: list[Opcion]
    tipos_captura: list[Opcion]
    paleta: dict[str, str]
    secuencia_colores: list[str]


class Variable(Esquema):
    nombre: str
    etiqueta: str
    descripcion: str
    tipo: TipoVariable
    rol: RolVariable
    usada_en_modelos: list[str]


class Atributos(Esquema):
    exceso_verde: float | None = None
    saturacion: float | None = None
    brillo: float | None = None
    contraste: float | None = None
    media_r: float | None = None
    media_g: float | None = None
    media_b: float | None = None
    nitidez: float | None = None
    megapixeles: float | None = None
    aspecto: float | None = None
    prop_sobreexpuesta: float | None = None
    prop_subexpuesta: float | None = None


class Conteo(Esquema):
    clave: str
    etiqueta: str
    conteo: int


class ResumenDatos(Esquema):
    total_registros: int
    registros_dr: int
    campos: int
    por_subconjunto: list[Conteo]
    por_temporada: list[Conteo]
    por_dano: list[Conteo]
    por_etapa: list[Conteo]
    magnitud_global: list[Conteo]
    magnitud_dr: list[Conteo]


class Registro(Esquema):
    id: str
    archivo: str
    temporada: Temporada
    etapa: Etapa | None
    dano: Dano
    magnitud: int
    subconjunto: Subconjunto
    tipo_captura: TipoCaptura | None
    atributos: Atributos


class PaginaRegistros(Esquema):
    total: int
    pagina: int
    tamano: int
    paginas: int
    registros: list[Registro]


class GrupoDistribucion(Esquema):
    grupo: str
    etiqueta: str
    conteos: list[int]


class Distribucion(Esquema):
    variable: str
    por: AgrupacionDatos
    bordes: list[float] = Field(description="Bordes compartidos por todos los grupos; hay uno mas que conteos.")
    grupos: list[GrupoDistribucion]


class PuntoDispersion(Esquema):
    id: str
    x: float
    y: float
    dano: Dano
    temporada: Temporada


class Dispersion(Esquema):
    x: str
    y: str
    total_disponible: int
    puntos: list[PuntoDispersion]


class Correlacion(Esquema):
    variable: str
    spearman: float | None
    n: int


class PasoAjuste(Esquema):
    parametros: dict[str, ValorHiperparametro]
    rmse_validacion: float = Field(description="RMSE de validacion sobre la magnitud en escala 0-100.")
    mae_validacion: float | None = Field(default=None, description="MAE de validacion sobre la magnitud en escala 0-100.")
    elegido: bool = Field(default=False, description="Verdadero si esta combinacion de hiperparametros fue la seleccionada.")


class EpocaEntrenamiento(Esquema):
    epoca: int
    perdida_entrenamiento: float = Field(description="MSE sobre la magnitud normalizada de 0 a 1.")
    perdida_validacion: float | None = Field(default=None, description="MSE sobre la magnitud normalizada de 0 a 1.")
    mae_validacion: float | None = Field(default=None, description="MAE de validacion sobre la magnitud en escala 0-100.")


class Importancia(Esquema):
    variable: str
    importancia: float


class ModeloInfo(Esquema):
    id: str
    nombre: str
    familia: Familia
    descripcion: str
    entradas: list[str]
    hiperparametros: dict[str, ValorHiperparametro]
    disponible: bool = Field(description="Existe el artefacto entrenado y puede usarse en /predecir.")
    tiene_resultados: bool = Field(description="Existen resultados de prueba para /metricas.")


class ModeloDetalle(ModeloInfo):
    historial_ajuste: list[PasoAjuste]
    curva_entrenamiento: list[EpocaEntrenamiento]
    importancias: list[Importancia]


class Metricas(Esquema):
    modelo_id: str
    alcance: Alcance
    n: int
    mae: float
    rmse: float
    r2: float | None
    tiempo_entrenamiento_s: float
    tiempo_inferencia_ms: float


class PuntoPrediccion(Esquema):
    id: str
    real: float
    predicho: float
    error: float = Field(description="predicho menos real.")
    temporada: Temporada
    etapa: Etapa | None
    dano: Dano


class ErrorGrupo(Esquema):
    grupo: str
    etiqueta: str
    n: int
    mae: float
    rmse: float


class PrediccionModelo(Esquema):
    modelo_id: str
    nombre: str
    magnitud: float = Field(ge=0, le=100)
    magnitud_redondeada: int = Field(ge=0, le=100, multiple_of=10)
    regla_aplicada: bool = Field(description="Verdadero si se devolvio 0 por un diagnostico distinto de DR.")
    tiempo_ms: float


class Prediccion(Esquema):
    dano_considerado: Dano | None
    atributos: Atributos
    predicciones: list[PrediccionModelo]
    advertencias: list[str]


class PrediccionGuardada(Esquema):
    id: str
    real: float
    predicho: float
    temporada: Temporada
    etapa: Etapa | None
    dano: Dano


class ResultadosModelo(Esquema):
    modelo_id: str
    tiempo_entrenamiento_s: float = Field(ge=0)
    tiempo_inferencia_ms: float = Field(ge=0)
    hiperparametros: dict[str, ValorHiperparametro]
    predicciones: list[PrediccionGuardada]
    historial_ajuste: list[PasoAjuste] = []
    curva_entrenamiento: list[EpocaEntrenamiento] = []
    importancias: list[Importancia] = []
