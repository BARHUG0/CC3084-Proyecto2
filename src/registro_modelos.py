from src.config import DIR_MODELOS
from src.modelos_densenet import DenseNetMagnitud
from src.modelos_resnet import ResNetAjustada, ResNetMagnitud
from src.modelos_tabulares import PredictorConstante, RandomForestMagnitud, RegresionExcesoVerde

CLASES_MODELOS = (
    PredictorConstante,
    RegresionExcesoVerde,
    RandomForestMagnitud,
    ResNetMagnitud,
    ResNetAjustada,
    DenseNetMagnitud,
)


def crear_registro(dir_modelos=DIR_MODELOS):
    return {clase.id: clase(dir_modelos) for clase in CLASES_MODELOS}
