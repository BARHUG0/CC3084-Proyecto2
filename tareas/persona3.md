# Persona 3: ResNet50, comparación de modelos y conclusiones

## Objetivo

Adaptar ResNet50 preentrenada para estimar la magnitud del daño por sequía, comparar todos los modelos con visualizaciones estáticas y redactar los resultados de modelado y las conclusiones del informe.

Esta tarea no depende de las otras dos. El cuaderno de comparación lee los resultados que existan en ese momento, por lo que puede construirse con el modelo constante y volver a ejecutarse cuando estén los demás.

## Preparación común

1. Activar el entorno del directorio superior e instalar dependencias:
   ```powershell
   uv pip install -r requirements.txt
   ```
2. Instalar PyTorch con CUDA si el equipo tiene GPU NVIDIA:
   ```powershell
   uv pip install --reinstall-package torch --reinstall-package torchvision torch torchvision --index-url https://download.pytorch.org/whl/cu130
   python -c "import torch; print(torch.cuda.is_available())"
   ```
3. Obtener los datos con el flujo existente del proyecto: descarga, `python -m src.caracteristicas` y el cuaderno `01_adquisicion_datos.ipynb`.
4. Crear el conjunto de modelado:
   ```powershell
   python -m src.conjunto
   ```
   La partición entre entrenamiento y prueba se agrupa por campo y usa una semilla fija. Todo el equipo obtiene la misma partición. No se debe modificar `src/particiones.py` ni `SEMILLA` en `src/config.py`.
5. Confirmar que las pruebas pasan antes de empezar:
   ```powershell
   pytest
   ```

## Reglas compartidas

- Se entrena únicamente con `subconjunto == "entrenamiento"`. El subconjunto `prueba` solo se usa una vez, al final, para guardar resultados.
- La validación interna separa campos: se usa el primer pliegue de `pliegues_por_campo(entrenamiento)` para detener el entrenamiento y comparar configuraciones.
- Los modelos estiman severidad condicionada a sequía. Se entrenan con `entrenamiento_y_prueba(conjunto, solo_dr=True)` y se evalúan con `completar_con_regla`, que asigna 0 a los diagnósticos distintos de DR.
- No se modifican `src/esquemas.py`, `src/api.py` ni `contrato/`. El contrato con el frontend ya está fijado.
- Cada modelo hereda de `ModeloMagnitud` en `src/modelo_base.py` y se agrega a `CLASES_MODELOS` en `src/registro_modelos.py`.
- `ejecutar_referencia_constante` en `src/modelos_tabulares.py` es el ejemplo completo a imitar.

## Procedimiento común de las redes convolucionales

DenseNet121 y ResNet50 deben entrenarse con este mismo procedimiento. Así la comparación refleja la arquitectura y no diferencias de configuración.

| Elemento | Valor |
|:--|:--|
| Pesos iniciales | ImageNet de `torchvision` |
| Tamaño de entrada | 224 x 224 |
| Transformación de evaluación | `Resize(256)`, `CenterCrop(224)` y normalización de ImageNet |
| Aumentos de entrenamiento | `RandomResizedCrop(224, scale=(0.7, 1.0))` y `RandomHorizontalFlip`. No se altera el tono, porque el color es parte de la señal del daño. |
| Objetivo | `magnitud / 100`; la predicción se multiplica por 100 |
| Salida | Una capa lineal con una neurona |
| Pérdida | `MSELoss` |
| Optimizador | `AdamW` con `weight_decay=1e-4` |
| Lote | 16, con precisión mixta `torch.autocast` |
| Épocas | Máximo 15, con parada temprana de paciencia 3 sobre la pérdida de validación |
| Búsqueda | Tasa de aprendizaje en `1e-4` y `3e-4`; descongelar `cabeza` o `ultimo_bloque` |
| Selección | Menor RMSE de validación; luego se reentrena con todo el entrenamiento DR durante las épocas elegidas |

## Entregables

### 1. Modelo en `src/modelos_resnet.py`

- Clase `ResNetMagnitud` con `id = "resnet50"`, `familia = "cnn"`, `entradas = ("imagen_rgb",)` y `extension = ".pt"`.
- El archivo es autosuficiente. Si `src/modelos_densenet.py` ya existe, sus utilidades pueden reutilizarse, pero no es requisito.
- El artefacto `.pt` guarda el `state_dict` y la configuración elegida.
- `cargar()` reconstruye la red sin descargar pesos, carga el `state_dict` y usa CUDA si está disponible.
- `predecir(imagen, atributos)` recibe una imagen PIL en RGB, aplica la transformación de evaluación y devuelve un número entre 0 y 100.
- Función `ejecutar_resnet(conjunto, dir_modelos, dir_resultados)` que ajusta, reentrena, guarda el artefacto y llama a `guardar_resultados` con `hiperparametros`, `historial_ajuste`, `curva_entrenamiento` y `tiempo_inferencia_ms`, igual que la DenseNet.

### 2. Registro

Agregar `ResNetMagnitud` a `CLASES_MODELOS`.

### 3. Cuaderno `notebooks/06_modelo_resnet.ipynb`

- Ejecuta el ajuste y el entrenamiento llamando funciones de `src/`.
- Guarda la figura `informe/figuras/06_curva_resnet.png`.

### 4. Cuaderno `notebooks/07_comparacion_modelos.ipynb`

Lee todos los modelos de `crear_registro()` que tengan resultados, mediante `cargar_resultados` y `tabla_predicciones` de `src/evaluacion.py`. Produce al menos estas figuras estáticas con la `PALETA` y `SECUENCIA_COLORES` de `src/config.py`:

- `informe/figuras/07_comparacion_errores.png`: MAE y RMSE por modelo, con alcance DR y global.
- `informe/figuras/07_real_vs_predicho.png`: magnitud real contra predicha, un panel por modelo.
- `informe/figuras/07_error_por_temporada.png`: RMSE por temporada y modelo.
- `informe/figuras/07_tiempos.png`: tiempo de entrenamiento e inferencia por modelo.

El cuaderno incluye una tabla final con MAE, RMSE, R² y tiempos, y una recomendación justificada del modelo o los modelos elegidos.

### 5. Informe

Redactar en `informe/secciones/`:

- `06_resultados_modelos.md`: ajuste de parámetros de cada algoritmo, a partir del `historial_ajuste` de cada resultado, y comparación por efectividad, errores y tiempos con las figuras del cuaderno 07.
- `08_conclusiones.md`: cumplimiento de cada objetivo de `02_objetivos.md` y discusión sobre la efectividad de los algoritmos.

El informe completo se genera con:
```powershell
quarto render informe/informe_final.md --to pdf
```

## Criterios de terminado

- `pytest` pasa.
- `uvicorn src.api:app` muestra `resnet50` con `disponible: true` y `tiene_resultados: true` en `/api/modelos`.
- El cuaderno 07 se ejecuta de principio a fin con los resultados disponibles y genera las cuatro figuras.
- Los archivos `data/procesado/modelos/resnet50.pt` y `data/procesado/resultados/resnet50.json` se comparten en la carpeta común del equipo, porque `data/` no se versiona.

## Commits sugeridos

- `feat: agrega resnet50 para regresion de magnitud`
- `feat: registra el modelo resnet50`
- `feat: agrega cuaderno de entrenamiento de resnet50`
- `feat: agrega cuaderno de comparacion de modelos`
- `docs: redacta resultados de modelado y conclusiones`
