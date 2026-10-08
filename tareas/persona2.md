# Persona 2: DenseNet121 y marco teórico

## Objetivo

Adaptar DenseNet121 preentrenada para estimar la magnitud del daño por sequía a partir de la fotografía RGB. También redactar el marco teórico, el análisis de los datos y las referencias del informe.

Esta tarea no depende de las otras dos. Puede hacerse en cualquier orden.

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

### 1. Modelo en `src/modelos_densenet.py`

- Clase `DenseNetMagnitud` con `id = "densenet121"`, `familia = "cnn"`, `entradas = ("imagen_rgb",)` y `extension = ".pt"`.
- El artefacto `.pt` guarda el `state_dict` y la configuración elegida.
- `cargar()` reconstruye la red sin descargar pesos, carga el `state_dict` y usa CUDA si está disponible.
- `predecir(imagen, atributos)` recibe una imagen PIL en RGB, aplica la transformación de evaluación y devuelve un número entre 0 y 100.
- Las imágenes del conjunto se leen desde `DIR_IMAGENES / ruta_relativa`.
- Función `ejecutar_densenet(conjunto, dir_modelos, dir_resultados)` que ajusta, reentrena, guarda el artefacto y llama a `guardar_resultados` con:
  - `hiperparametros`: tasa de aprendizaje, capas descongeladas y épocas.
  - `historial_ajuste`: una entrada por configuración, con `rmse_validacion` y `mae_validacion` en la escala de 0 a 100.
  - `curva_entrenamiento`: una entrada por época de la configuración elegida.
  - `tiempo_inferencia_ms`: tiempo medio por imagen sobre la prueba DR.

### 2. Registro

Agregar `DenseNetMagnitud` a `CLASES_MODELOS`.

### 3. Cuaderno `notebooks/05_modelo_densenet.ipynb`

- Ejecuta el ajuste y el entrenamiento llamando funciones de `src/`.
- Muestra la tabla de configuraciones probadas.
- Guarda la figura `informe/figuras/05_curva_densenet.png` con la `PALETA` de `src/config.py`.

### 4. Informe

Redactar en `informe/secciones/`:

- `03_marco_teorico.md`: procesamiento de imágenes, análisis de imágenes desde el punto de vista agrícola y algoritmos útiles para el problema. Se reutiliza y condensa `informe/revision_bibliografica.md`.
- `05_resultados_datos.md`: características del conjunto original, limpieza, preprocesamiento y análisis exploratorio. Se apoya en los cuadernos 01 a 03 y en las figuras existentes de `informe/figuras/`.
- `09_referencias.md`: referencias en formato APA de todo el informe. Las demás personas agregan aquí las que citen.

El informe completo se genera con:
```powershell
quarto render informe/informe_final.md --to pdf
```

## Criterios de terminado

- `pytest` pasa.
- `uvicorn src.api:app` muestra `densenet121` con `disponible: true` y `tiene_resultados: true` en `/api/modelos`.
- `POST /api/predecir` con `modelos=densenet121` responde en `/docs` con una fotografía real.
- Los archivos `data/procesado/modelos/densenet121.pt` y `data/procesado/resultados/densenet121.json` se comparten en la carpeta común del equipo, porque `data/` no se versiona.

## Commits sugeridos

- `feat: agrega densenet121 para regresion de magnitud`
- `feat: registra el modelo densenet121`
- `feat: agrega cuaderno de entrenamiento de densenet121`
- `docs: redacta marco teorico`
- `docs: redacta resultados del analisis de datos`
