from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]

DIR_DATOS = RAIZ / "data"
DIR_CRUDO = DIR_DATOS / "crudo"
DIR_IMAGENES = DIR_DATOS / "imagenes"
DIR_PROCESADO = DIR_DATOS / "procesado"
DIR_INFORME = RAIZ / "informe"
DIR_FIGURAS = DIR_INFORME / "figuras"

SERVICIO_KEYRING = "cgiar-eyes-on-the-ground"
CLAVE_TOKEN = "zindi_auth_token"

COMPETENCIA = "cgiar-eyes-on-the-ground-challenge"
URL_ARCHIVOS_ZINDI = f"https://api.zindi.world/v1/competitions/{COMPETENCIA}/files"
CARPETA_DRIVE = "https://drive.google.com/drive/folders/1O2M-SZV5cKGuVA8XwxlAgd5Fs4VpzRDS"

ARCHIVOS_ZINDI = ("Train.csv", "Test.csv", "SampleSubmission.csv")
ARCHIVOS_DRIVE = ("train.zip", "test.zip")

CONTEO_OFICIAL_TEMPORADA = {
    "LR2020": 2034,
    "LR2021": 7979,
    "SR2020": 6163,
    "SR2021": 9930,
}

TEMPORADAS = ("LR2020", "SR2020", "LR2021", "SR2021")

ETAPAS_CRECIMIENTO = {
    "S": "Siembra",
    "V": "Vegetativa",
    "F": "Floracion",
    "M": "Madurez",
}

TIPOS_DANO = {
    "DR": "Sequia",
    "DS": "Enfermedad",
    "FD": "Inundacion",
    "G": "Crecimiento sano",
    "ND": "Deficiencia de nutrientes",
    "PS": "Plaga",
    "WD": "Maleza",
    "WN": "Viento",
}

ORDEN_ETAPAS = ("S", "V", "F", "M")
ORDEN_DANOS = ("G", "DR", "DS", "FD", "ND", "PS", "WD", "WN")

TIPOS_CAPTURA = {
    "inicial": "Fotografia de referencia inicial",
    "seguimiento": "Fotografia de seguimiento periodico",
    "reclamo": "Fotografia de reclamo",
}
ORDEN_TIPOS_CAPTURA = ("inicial", "seguimiento", "reclamo")

EXTENSIONES_IMAGEN = (".jpg", ".jpeg", ".png")

LADO_MINIATURA = 256
UMBRAL_SOBREEXPUESTO = 245
UMBRAL_SUBEXPUESTO = 10
UMBRAL_NITIDEZ = 100.0
DISTANCIA_HAMMING_MAXIMA = 3

PALETA = {
    "principal": "#2E6F40",
    "secundario": "#C9A227",
    "terciario": "#8C3B2E",
    "neutro": "#4A4A4A",
    "claro": "#B8C9BC",
}

SECUENCIA_COLORES = (
    "#2E6F40",
    "#C9A227",
    "#8C3B2E",
    "#3C6E93",
    "#7A5C99",
    "#B87333",
    "#5B8C5A",
    "#A6A6A6",
)


def asegurar_directorios():
    for ruta in (DIR_CRUDO, DIR_IMAGENES, DIR_PROCESADO, DIR_FIGURAS):
        ruta.mkdir(parents=True, exist_ok=True)
