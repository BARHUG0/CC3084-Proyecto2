import pandas as pd
from PIL import Image

from src.datos_sinteticos import crear_entorno
from src.evaluacion import cargar_resultados
from src.modelos_resnet import ejecutar_resnet
from src.registro_modelos import crear_registro


def test_resnet_entrena_guarda_y_predice(tmp_path):
    almacen = crear_entorno(tmp_path)
    conjunto = pd.read_parquet(almacen.ruta_conjunto)
    ejecutar_resnet(
        conjunto, almacen.dir_modelos, almacen.dir_resultados, almacen.dir_imagenes,
        tasas=(1e-4,), descongelar=("cabeza",), epocas_maximas=1, pesos=None,
    )

    resultados = cargar_resultados("resnet50", almacen.dir_resultados)
    assert len(resultados.predicciones) == (conjunto["subconjunto"] == "prueba").sum()
    assert [paso.elegido for paso in resultados.historial_ajuste] == [True]
    assert len(resultados.curva_entrenamiento) == 1

    modelo = crear_registro(almacen.dir_modelos)["resnet50"]
    assert modelo.disponible
    with Image.open(next((almacen.dir_imagenes / "train").iterdir())) as imagen:
        magnitud, regla = modelo.estimar(imagen.convert("RGB"), {}, "DR")
    assert 0 <= magnitud <= 100 and not regla
