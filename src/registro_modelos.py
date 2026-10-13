from src.config import DIR_MODELOS
from src.modelos_resnet import ResNetMagnitud
from src.modelos_tabulares import PredictorConstante

CLASES_MODELOS = (PredictorConstante, ResNetMagnitud)


def crear_registro(dir_modelos=DIR_MODELOS):
    return {clase.id: clase(dir_modelos) for clase in CLASES_MODELOS}
