from abc import ABC, abstractmethod
from pathlib import Path

from src.config import DANO_SEQUIA, DIR_MODELOS

MAGNITUD_MINIMA = 0.0
MAGNITUD_MAXIMA = 100.0


def acotar_magnitud(valor):
    return float(min(MAGNITUD_MAXIMA, max(MAGNITUD_MINIMA, float(valor))))


class ModeloMagnitud(ABC):
    id = ""
    nombre = ""
    familia = "tabular"
    descripcion = ""
    entradas = ()
    extension = ".joblib"

    def __init__(self, dir_modelos=DIR_MODELOS):
        self.ruta_artefacto = Path(dir_modelos) / f"{self.id}{self.extension}"
        self._cargado = False

    @property
    def disponible(self):
        return self.ruta_artefacto.exists()

    @abstractmethod
    def cargar(self):
        ...

    @abstractmethod
    def predecir(self, imagen, atributos):
        ...

    def estimar(self, imagen, atributos, dano=None):
        if dano is not None and dano != DANO_SEQUIA:
            return 0.0, True
        if not self._cargado:
            self.cargar()
            self._cargado = True
        return acotar_magnitud(self.predecir(imagen, atributos)), False
