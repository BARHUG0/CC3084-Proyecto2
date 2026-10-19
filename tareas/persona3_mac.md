# Persona 3 en Mac con Apple Silicon

Guía para ejecutar la tarea de `persona3.md` en una Mac con chip Apple. Se usó una MacBook Pro con M5 Pro, GPU de 16 núcleos y 24 GB de memoria unificada. El procedimiento de entrenamiento es el mismo que en `persona3.md`. Solo cambia el dispositivo: la GPU se usa mediante Metal (`mps`) en lugar de CUDA.

## Entorno

```bash
cd ..                                   # directorio superior del repositorio
uv venv .venv --python 3.13
source .venv/bin/activate
cd CC3084-Proyecto2
uv pip install -r requirements.txt
python -c "import torch; print(torch.__version__, torch.backends.mps.is_available())"
pytest
```

- El paquete de PyTorch para macOS ya incluye soporte `mps`, así que no aplica el paso de CUDA de la preparación común.
- Se usa Python 3.13 porque `contrato/openapi.json` se exportó con esa versión. Con 3.12, las frases de estado HTTP cambian ("Unprocessable Entity" en vez de "Unprocessable Content") y la prueba del contrato falla.
- Si `jupyter nbconvert` falla con `Kernel died before replying to kernel_info`, el kernel global `python3` apunta a otro entorno. Use el kernel del entorno virtual:
  ```bash
  JUPYTER_PATH=../.venv/share/jupyter jupyter nbconvert --to notebook --execute <cuaderno>
  ```

## Datos

1. Ejecute `python -m src.descarga imagenes`. No requiere token. Descarga 8.7 GB de Google Drive y tarda unos 15 minutos.
2. Consiga los CSV con una de estas dos opciones:
   - Descargue `Train.csv`, `Test.csv` y `SampleSubmission.csv` desde la pestaña Data de Zindi y cópielos a `data/crudo/`.
   - Guarde el token con `python -m src.credenciales guardar` y luego ejecute `python -m src.descarga csv`.
3. Ejecute `python -m src.descarga verificar`.
4. Ejecute `python -m src.caracteristicas --particion todas`. Tarda unos 45 segundos con 34 731 imágenes.
5. Ejecute el cuaderno `01_adquisicion_datos.ipynb` y luego `python -m src.conjunto`.

El conjunto de modelado queda con 23 350 registros. De ellos, 4 489 son DR:

| Subconjunto | Registros DR | Campos |
|:--|--:|--:|
| Entrenamiento | 3 655 | 1 453 |
| Prueba | 834 | |

## Entrenamiento

```bash
caffeinate -i jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=-1 notebooks/06_modelo_resnet.ipynb
```

`caffeinate -i` evita que la Mac se suspenda durante el entrenamiento.

## Adaptaciones en `src/modelos_resnet.py`

| Aspecto | Decisión | Motivo |
|:--|:--|:--|
| Dispositivo | `cuda`, luego `mps`, luego `cpu` | El mismo código corre en Windows con NVIDIA y en Mac |
| Precisión mixta | `torch.autocast` con `bfloat16` en `mps` y en CUDA compatible | En el M5 Pro duplica el rendimiento y no requiere `GradScaler` |
| Lectura de imágenes | `Image.draft` decodifica el JPEG a escala reducida, como en `src/caracteristicas.py` | Las fotos son de varios megapíxeles |
| Procesos de carga | Contexto `forkserver` cuando existe | En macOS, con `spawn`, cada proceso tarda unos 5 s en cerrarse |
| BatchNorm | La parte congelada queda en modo `eval` | Con lotes de 16, las estadísticas de ImageNet son más estables |
| Pesos | `IMAGENET1K_V1` | Su transformación oficial es `Resize(256)` y coincide con DenseNet121, que solo tiene V1 |

## Rendimiento medido en el M5 Pro

| Medición | Resultado |
|:--|--:|
| Entrenamiento de la `cabeza`, `bfloat16` / `float32` | 314 / 227 imágenes por segundo |
| Entrenamiento del `ultimo_bloque`, `bfloat16` / `float32` | 363 / 169 imágenes por segundo |
| Inferencia, `bfloat16` / `float32` | 392 / 214 imágenes por segundo |
| Lectura y aumentos de imágenes reales con 8 procesos | 975 imágenes por segundo |
| Una época real (3 655 imágenes, `ultimo_bloque`) | 14 segundos, 254 imágenes por segundo |

Los tiempos de entrenamiento e inferencia que se guardan en `resnet50.json` corresponden a este equipo. El campo `dispositivo` de los hiperparámetros indica dónde se entrenó cada modelo. Los tiempos solo son comparables en orden de magnitud con modelos entrenados en otro hardware.

## Archivos para compartir

`data/` no se versiona. Copie estos archivos a la carpeta común del equipo:

- `data/procesado/modelos/resnet50.pt`
- `data/procesado/resultados/resnet50.json`

## ResNet50 ajustada

`resnet50_ajustada` es una segunda versión de la red con otra receta de entrenamiento. La `resnet50` original no cambia: sigue el procedimiento común y es la que se compara con DenseNet121.

La receta y la evidencia que la respalda están en el cuaderno `06b_modelo_resnet_ajustada.ipynb` y en la sección 6.4 del informe.

Para entrenarla:

```bash
caffeinate -is jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=-1 notebooks/06b_modelo_resnet_ajustada.ipynb
```

- **Duración:** unos 32 minutos con el cargador conectado. Entrena en el pliegue de validación con 224 y con 320, y luego reentrena con todo el entrenamiento DR.
- **Batería:** si la batería se agota, macOS suspende la computadora aunque `caffeinate` esté activo. El proceso se pausa y continúa al conectar el cargador, pero el tiempo de entrenamiento registrado queda inflado.

Archivos para compartir:

- `data/procesado/modelos/resnet50_ajustada.pt`
- `data/procesado/resultados/resnet50_ajustada.json`
