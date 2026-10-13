import multiprocessing
import os
import time
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from torch import nn
from torch.utils.data import DataLoader, Dataset
from torchvision import models, transforms

from src.config import DIR_IMAGENES, DIR_MODELOS, DIR_RESULTADOS, SEMILLA
from src.evaluacion import completar_con_regla, guardar_resultados, metricas
from src.modelo_base import ModeloMagnitud
from src.particiones import entrenamiento_y_prueba, pliegues_por_campo

LADO_ENTRADA = 224
LADO_DECODIFICACION = 512
MEDIA_IMAGENET = (0.485, 0.456, 0.406)
DESVIACION_IMAGENET = (0.229, 0.224, 0.225)

TRANSFORMACION_EVALUACION = transforms.Compose(
    [
        transforms.Resize(256),
        transforms.CenterCrop(LADO_ENTRADA),
        transforms.ToTensor(),
        transforms.Normalize(MEDIA_IMAGENET, DESVIACION_IMAGENET),
    ]
)
TRANSFORMACION_ENTRENAMIENTO = transforms.Compose(
    [
        transforms.RandomResizedCrop(LADO_ENTRADA, scale=(0.7, 1.0)),
        transforms.RandomHorizontalFlip(),
        transforms.ToTensor(),
        transforms.Normalize(MEDIA_IMAGENET, DESVIACION_IMAGENET),
    ]
)

PESOS_IMAGENET = models.ResNet50_Weights.IMAGENET1K_V1
TASAS_APRENDIZAJE = (1e-4, 3e-4)
DESCONGELAR = ("cabeza", "ultimo_bloque")
TAMANO_LOTE = 16
EPOCAS_MAXIMAS = 15
PACIENCIA = 3
DECAIMIENTO_PESOS = 1e-4
# Con spawn (macOS) cada worker tarda ~5 s en cerrar; forkserver no existe en Windows.
CONTEXTO_WORKERS = "forkserver" if "forkserver" in multiprocessing.get_all_start_methods() else None


def dispositivo():
    if torch.cuda.is_available():
        return torch.device("cuda")
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def _sincronizar(disp):
    if disp.type == "cuda":
        torch.cuda.synchronize()
    elif disp.type == "mps":
        torch.mps.synchronize()


def _liberar(disp):
    if disp.type == "cuda":
        torch.cuda.empty_cache()
    elif disp.type == "mps":
        torch.mps.empty_cache()


def abrir_imagen(ruta):
    # draft decodifica el JPEG a escala reducida; las fotos originales tienen varios megapixeles.
    with Image.open(ruta) as imagen:
        imagen.draft("RGB", (LADO_DECODIFICACION, LADO_DECODIFICACION))
        return imagen.convert("RGB")


class ImagenesMagnitud(Dataset):
    def __init__(self, df, dir_imagenes, transformacion):
        self.rutas = [Path(dir_imagenes) / ruta for ruta in df["ruta_relativa"]]
        self.objetivos = df["magnitud"].to_numpy(dtype=np.float32) / 100
        self.transformacion = transformacion

    def __len__(self):
        return len(self.rutas)

    def __getitem__(self, indice):
        return self.transformacion(abrir_imagen(self.rutas[indice])), self.objetivos[indice]


def _cargador(df, dir_imagenes, transformacion, mezclar):
    lotes = -(-len(df) // TAMANO_LOTE)
    trabajadores = max(0, min(8, (os.cpu_count() or 1) - 2, lotes))
    return DataLoader(
        ImagenesMagnitud(df, dir_imagenes, transformacion),
        batch_size=TAMANO_LOTE,
        shuffle=mezclar,
        num_workers=trabajadores,
        persistent_workers=trabajadores > 0,
        multiprocessing_context=CONTEXTO_WORKERS if trabajadores > 0 else None,
    )


def construir_red(pesos=None, descongelar="cabeza"):
    red = models.resnet50(weights=pesos)
    for parametro in red.parameters():
        parametro.requires_grad = False
    red.fc = nn.Linear(red.fc.in_features, 1)
    if descongelar == "ultimo_bloque":
        for parametro in red.layer4.parameters():
            parametro.requires_grad = True
    return red


def _modo_entrenamiento(red, descongelar):
    # La parte congelada queda en eval para que BatchNorm conserve las estadisticas de ImageNet.
    red.eval()
    red.fc.train()
    if descongelar == "ultimo_bloque":
        red.layer4.train()


def _entrenar_epoca(red, cargador, optimizador, descongelar, disp):
    _modo_entrenamiento(red, descongelar)
    criterio = nn.MSELoss()
    total = torch.zeros((), device=disp)
    for imagenes, objetivos in cargador:
        imagenes, objetivos = imagenes.to(disp), objetivos.to(disp)
        with torch.autocast(device_type=disp.type, dtype=torch.bfloat16):
            salida = red(imagenes).squeeze(1)
        perdida = criterio(salida.float(), objetivos)
        optimizador.zero_grad(set_to_none=True)
        perdida.backward()
        optimizador.step()
        total += perdida.detach() * len(objetivos)
    return float(total) / len(cargador.dataset)


@torch.no_grad()
def _predecir_cargador(red, cargador, disp):
    red.eval()
    salidas = [red(imagenes.to(disp)).squeeze(1) for imagenes, _ in cargador]
    return torch.cat(salidas).float().cpu().numpy()


def _ajustar(entrenamiento, validacion, tasa, descongelar, epocas, pesos, dir_imagenes, disp):
    torch.manual_seed(SEMILLA)
    red = construir_red(pesos, descongelar).to(disp)
    optimizador = torch.optim.AdamW(
        [p for p in red.parameters() if p.requires_grad], lr=tasa, weight_decay=DECAIMIENTO_PESOS
    )
    cargador_entrenamiento = _cargador(entrenamiento, dir_imagenes, TRANSFORMACION_ENTRENAMIENTO, mezclar=True)
    cargador_validacion = None
    if validacion is not None:
        cargador_validacion = _cargador(validacion, dir_imagenes, TRANSFORMACION_EVALUACION, mezclar=False)
        real = validacion["magnitud"].to_numpy(dtype=float)

    curva, mejor, sin_mejora = [], None, 0
    for epoca in range(1, epocas + 1):
        inicio = time.perf_counter()
        punto = {"epoca": epoca, "perdida_entrenamiento": _entrenar_epoca(red, cargador_entrenamiento, optimizador, descongelar, disp)}
        if cargador_validacion is not None:
            predicho = _predecir_cargador(red, cargador_validacion, disp)
            valores = metricas(real, np.clip(100 * predicho, 0, 100))
            punto["perdida_validacion"] = float(np.mean((predicho - real / 100) ** 2))
            punto["mae_validacion"] = valores["mae"]
        curva.append(punto)
        print(f"  epoca {epoca}: {punto} ({time.perf_counter() - inicio:.0f} s)", flush=True)
        if cargador_validacion is None:
            continue
        if mejor is None or punto["perdida_validacion"] < mejor["perdida"]:
            mejor = {"epoca": epoca, "perdida": punto["perdida_validacion"], "rmse": valores["rmse"], "mae": valores["mae"]}
            sin_mejora = 0
        else:
            sin_mejora += 1
            if sin_mejora >= PACIENCIA:
                break
    return red, curva, mejor


class ResNetMagnitud(ModeloMagnitud):
    id = "resnet50"
    nombre = "ResNet50"
    familia = "cnn"
    descripcion = "ResNet50 preentrenada en ImageNet con una salida lineal para la magnitud del dano por sequia."
    entradas = ("imagen_rgb",)
    extension = ".pt"

    def __init__(self, dir_modelos=DIR_MODELOS):
        super().__init__(dir_modelos)
        self.dispositivo = dispositivo()
        self.red = None
        self.configuracion = {}

    def guardar(self):
        self.ruta_artefacto.parent.mkdir(parents=True, exist_ok=True)
        torch.save({"state_dict": self.red.state_dict(), "configuracion": self.configuracion}, self.ruta_artefacto)

    def cargar(self):
        artefacto = torch.load(self.ruta_artefacto, map_location=self.dispositivo)
        self.configuracion = artefacto["configuracion"]
        self.red = construir_red()
        self.red.load_state_dict(artefacto["state_dict"])
        self.red.to(self.dispositivo).eval()

    @torch.no_grad()
    def predecir(self, imagen, atributos):
        tensor = TRANSFORMACION_EVALUACION(imagen.convert("RGB")).unsqueeze(0).to(self.dispositivo)
        return 100 * float(self.red(tensor).squeeze())

    def predecir_lote(self, df, dir_imagenes=DIR_IMAGENES):
        cargador = _cargador(df, dir_imagenes, TRANSFORMACION_EVALUACION, mezclar=False)
        return 100 * _predecir_cargador(self.red, cargador, self.dispositivo)


def ejecutar_resnet(
    conjunto,
    dir_modelos=DIR_MODELOS,
    dir_resultados=DIR_RESULTADOS,
    dir_imagenes=DIR_IMAGENES,
    tasas=TASAS_APRENDIZAJE,
    descongelar=DESCONGELAR,
    epocas_maximas=EPOCAS_MAXIMAS,
    pesos=PESOS_IMAGENET,
):
    entrenamiento, prueba = entrenamiento_y_prueba(conjunto, solo_dr=True)
    indices_ajuste, indices_validacion = pliegues_por_campo(entrenamiento)[0]
    ajuste, validacion = entrenamiento.iloc[indices_ajuste], entrenamiento.iloc[indices_validacion]
    disp = dispositivo()
    print(f"Dispositivo: {disp.type}. Ajuste: {len(ajuste)}, validacion: {len(validacion)}, prueba DR: {len(prueba)}")

    inicio = time.perf_counter()
    historial, curvas = [], []
    for tasa in tasas:
        for capas in descongelar:
            print(f"Configuracion: tasa={tasa}, descongelar={capas}", flush=True)
            _, curva, mejor = _ajustar(ajuste, validacion, tasa, capas, epocas_maximas, pesos, dir_imagenes, disp)
            historial.append(
                {
                    "parametros": {"tasa_aprendizaje": tasa, "descongelar": capas, "epocas": mejor["epoca"]},
                    "rmse_validacion": mejor["rmse"],
                    "mae_validacion": mejor["mae"],
                }
            )
            curvas.append(curva)
            _liberar(disp)
    elegido = min(range(len(historial)), key=lambda i: historial[i]["rmse_validacion"])
    historial[elegido]["elegido"] = True
    parametros = historial[elegido]["parametros"]

    print(f"Reentrenamiento con todo el entrenamiento DR: {parametros}", flush=True)
    modelo = ResNetMagnitud(dir_modelos)
    modelo.red, _, _ = _ajustar(
        entrenamiento, None, parametros["tasa_aprendizaje"], parametros["descongelar"], parametros["epocas"],
        pesos, dir_imagenes, disp,
    )
    tiempo_entrenamiento_s = time.perf_counter() - inicio
    modelo.configuracion = dict(parametros)
    modelo.guardar()

    _, prueba_completa = entrenamiento_y_prueba(conjunto)
    inicio = time.perf_counter()
    predicho_dr = modelo.predecir_lote(prueba, dir_imagenes)
    _sincronizar(disp)
    tiempo_inferencia_ms = 1000 * (time.perf_counter() - inicio) / max(1, len(prueba))

    return guardar_resultados(
        modelo_id=modelo.id,
        prueba=prueba_completa,
        predicho=completar_con_regla(prueba_completa, predicho_dr),
        tiempo_entrenamiento_s=tiempo_entrenamiento_s,
        tiempo_inferencia_ms=tiempo_inferencia_ms,
        hiperparametros={**parametros, "dispositivo": disp.type, "pesos": pesos.name if pesos else None},
        historial_ajuste=historial,
        curva_entrenamiento=curvas[elegido],
        dir_resultados=dir_resultados,
    )
