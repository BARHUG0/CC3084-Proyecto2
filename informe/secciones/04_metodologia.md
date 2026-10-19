## 4. Metodología

### 4.1 Pasos seguidos

1. **Adquisición.** Los CSV se descargan desde la API de Zindi con un token personal guardado en el almacén de credenciales del sistema. Las fotografías se descargan desde la carpeta compartida de la competencia en Google Drive. Una verificación confirma que cada registro tiene su fotografía y que no hay fotografías sin registro.
2. **Extracción de atributos.** Cada fotografía se describe con doce atributos globales:
   - exceso de verde (2g − r − b);
   - saturación, brillo y contraste;
   - medias de los canales rojo, verde y azul;
   - nitidez (varianza del laplaciano);
   - proporciones de píxeles sobreexpuestos y subexpuestos;
   - megapíxeles y relación de aspecto.
   Los diez primeros se calculan sobre una miniatura de 256 píxeles de lado; los dos últimos, sobre las dimensiones originales. El resultado se guarda en una caché reanudable.
3. **Limpieza.** Un registro es apto para modelado si cumple seis condiciones: su fotografía existe; no es una copia; la magnitud es un múltiplo de 10 entre 0 y 100; la etiqueta es coherente (solo los diagnósticos de sequía tienen magnitud positiva, y se descartan los de sequía con magnitud 0); y la temporada y el campo están identificados.
4. **Conjunto de modelado.** Los registros aptos de `Train.csv` cuyos atributos se calcularon sin error se unen en un único archivo, que fija la partición entre entrenamiento y prueba para todo el equipo.
5. **Modelado.** Cada integrante entrena sus modelos con las mismas reglas de partición, validación y evaluación, y guarda los resultados de prueba en un formato común.
6. **Comparación y aplicación.** Un cuaderno de comparación lee los resultados de todos los modelos. La API y la aplicación web los presentan y permiten estimar la magnitud de una fotografía nueva.

### 4.2 Selección de los conjuntos de entrenamiento y prueba

La partición separa campos y no fotografías, porque el análisis exploratorio mostró que una partición aleatoria deja casi toda la validación en campos ya vistos.

- **Prueba.** El 20 % de los campos se asigna a prueba con `GroupShuffleSplit` y semilla 42. El resto queda para entrenamiento. La prueba se usa una sola vez por modelo, después de fijar sus hiperparámetros.
- **Validación.** El ajuste de hiperparámetros usa cinco pliegues agrupados por campo (`GroupKFold`) dentro del entrenamiento. Las redes convolucionales usan el primero de esos pliegues para la parada temprana y la selección de configuración.
- **Alcance del modelado.** Los modelos se entrenan solo con los registros de sequía (DR), porque son los únicos con magnitud distinta de cero. Al evaluar, una regla fija asigna 0 a los registros con otro diagnóstico. Las métricas (MAE, RMSE y R² en la escala de 0 a 100) se reportan sobre los registros DR de prueba y sobre la prueba completa.
- **Generalización temporal.** Como experimento adicional, dentro del entrenamiento DR, el Random Forest se entrena con las temporadas anteriores a SR2021 y se evalúa en SR2021. Este experimento no usa la prueba.

### 4.3 Selección de algoritmos

| Modelo | Familia | Entradas | Justificación |
|:--|:--|:--|:--|
| Predictor constante | Referencia | Ninguna | Predice la magnitud media del entrenamiento DR. Es el error mínimo que cualquier modelo debe superar. |
| Regresión lineal | Referencia | Exceso de verde | El exceso de verde es el atributo con mayor correlación con la magnitud (Spearman cercano a −0.25), y el análisis exploratorio recomendó usarlo como línea base. |
| Random Forest | Tabular | Nueve atributos globales | Capta relaciones no lineales e interacciones entre atributos, es robusto a escalas distintas y reporta la importancia de cada atributo. |
| DenseNet121 y ResNet50 | Red convolucional | Fotografía RGB | Aprenden textura y contexto de la escena, que los atributos globales no capturan. Parten de pesos preentrenados en ImageNet. |

El Random Forest usa nueve atributos: exceso de verde, saturación, brillo, contraste, las tres medias de canal y las dos proporciones de exposición. Excluye `megapixeles` y `nitidez` porque cambian con la temporada y pueden describir el teléfono más que el daño. El cuaderno 04 compara ambas variantes con la validación por campo.

Sus hiperparámetros se buscan con `RandomizedSearchCV`: 30 combinaciones, con la métrica `neg_root_mean_squared_error`, sobre este espacio:

- `n_estimators`: 100, 200, 300 y 500;
- `max_depth`: sin límite, 5, 10 y 20;
- `min_samples_leaf`: 1, 2, 5, 10, 20 y 50;
- `max_features`: raíz cuadrada, 0.5 y 1.0.

La combinación elegida se reajusta con todo el entrenamiento DR.

Las dos redes siguen el mismo procedimiento, para que la comparación entre ellas refleje la arquitectura y no la configuración:

| Elemento | Valor |
|:--|:--|
| Entrada | 224 × 224; para evaluar, `Resize(256)`, `CenterCrop(224)` y normalización de ImageNet |
| Aumentos | `RandomResizedCrop(224, scale=(0.7, 1.0))` y reflejo horizontal, sin alterar el tono |
| Objetivo y salida | Magnitud dividida entre 100, con una neurona lineal |
| Pérdida y optimizador | `MSELoss` y `AdamW` con `weight_decay=1e-4` |
| Lote y épocas | 16, con precisión mixta; máximo 15 épocas y parada temprana de paciencia 3 |
| Búsqueda | Tasa de aprendizaje de 1e-4 o 3e-4; se entrena la cabeza o también el último bloque |

Además se entrenó una variante ajustada de ResNet50, descrita en la sección 6.6.

### 4.4 Medición del costo computacional

- **Tiempo de entrenamiento.** Incluye la búsqueda de hiperparámetros completa y el reajuste final.
- **Tiempo de inferencia.** Es el promedio por fotografía sobre los registros DR de prueba.
  - En los modelos tabulares parte de los atributos ya calculados, así que no incluye su extracción.
  - En las redes incluye la lectura de la fotografía.

Para que los tiempos sean comparables, los seis modelos finales se entrenaron y evaluaron en el mismo equipo.

### 4.5 Recursos de cómputo

Los seis modelos finales se entrenaron en una laptop con procesador Intel Core i9-13980HX (24 núcleos, 32 hilos), 16 GB de RAM y GPU NVIDIA GeForce RTX 4050 de 6 GB, con Linux (CachyOS), Python 3.14, PyTorch 2.14 y CUDA 13.0.

| Modelos | Recurso | Uso |
|:--|:--|:--|
| Predictor constante, regresión y Random Forest | CPU | La búsqueda del Random Forest valida las combinaciones en paralelo. |
| ResNet50, ResNet50 ajustada y DenseNet121 | GPU mediante CUDA | Precisión mixta `bfloat16` y lectura de las fotografías con varios procesos en paralelo. |

El desarrollo se repartió entre los equipos de los integrantes. La receta de la ResNet50 ajustada se diseñó en una MacBook Pro con chip M5 Pro, usando la GPU mediante Metal (`mps`), y los modelos tabulares se desarrollaron en una laptop con AMD Ryzen 7 8845HS. El código detecta el dispositivo disponible, por lo que los mismos cuadernos funcionan en CUDA, en Metal o solo en CPU.

### 4.6 Lenguajes, herramientas y bibliotecas

- **Análisis y modelado:** Python 3.11 o superior.
  - pandas, NumPy, SciPy y PyArrow para los datos.
  - Pillow para las imágenes.
  - scikit-learn y joblib para los modelos tabulares.
  - PyTorch y torchvision para las redes.
  - Matplotlib para las figuras.
  - JupyterLab para los cuadernos.
  - pytest para las pruebas automáticas.
- **Datos:** requests y gdown para la descarga, y keyring para guardar el token fuera del código.
- **API:** FastAPI, Pydantic y Uvicorn.
- **Aplicación web:**
  - TypeScript y React con Vite.
  - Tailwind CSS y componentes de Radix para la interfaz.
  - Recharts para los gráficos.
  - TanStack Query para las consultas.
  - openapi-typescript y openapi-fetch para el cliente tipado.
- **Informe y versiones:** Quarto para el informe, y Git con GitHub para el control de versiones.

### 4.7 Justificación de FastAPI y React

- **FastAPI.** Permite servir los modelos en el mismo lenguaje en que se entrenan, sin traducirlos a otro entorno. Sus esquemas de Pydantic validan cada petición y cada respuesta, y generan el contrato OpenAPI que comparten el backend y el frontend. Así, un cambio en el contrato se detecta en las pruebas antes de llegar a la interfaz. También maneja la carga de archivos que necesita la estimación de una fotografía nueva.
- **React.** Organiza la interfaz en componentes reutilizables entre las cinco páginas de la aplicación. Con TypeScript y los tipos generados desde el contrato OpenAPI, el frontend falla al compilar si usa un campo que la API no ofrece. Su ecosistema aporta gráficos interactivos (Recharts) y manejo de consultas con caché (TanStack Query) sin desarrollarlos desde cero.
