## 3. Marco teórico

### 3.1 Procesamiento de imágenes digitales

Una fotografía digital en color es una matriz de píxeles con tres canales, rojo, verde y azul (RGB). En las fotografías del proyecto cada canal toma valores enteros de 0 a 255. Las operaciones de procesamiento transforman esa matriz para describirla, corregirla o prepararla como entrada de un modelo. Este proyecto usa dos familias de operaciones: la extracción de atributos globales y la preparación de la imagen completa para una red convolucional.

**Atributos fotométricos.** Resumen una imagen en pocos números interpretables. El brillo es la luminancia media y el contraste, su desviación estándar. La saturación mide la pureza del color en el espacio HSV, y las medias por canal describen el tono dominante. Las proporciones de píxeles sobreexpuestos o subexpuestos señalan problemas de iluminación.

Para la vegetación se usa el índice de exceso de verde, $ExG = 2g - r - b$, calculado sobre los canales normalizados por la suma $r + g + b$. Woebbecke et al. (1995) lo propusieron para separar plantas del suelo y de los residuos con imágenes de color. Su ventaja es que solo requiere una cámara RGB, a diferencia de índices como el NDVI, que necesitan una banda infrarroja (Cho et al., 2024).

**Calidad de captura.** La nitidez se estima con la varianza del laplaciano de la luminancia: una imagen enfocada tiene bordes marcados y, por tanto, una varianza alta. Los atributos que dependen de la escala, como la nitidez, se calculan sobre una miniatura de tamaño fijo. Sin esa normalización, reflejarían la resolución del archivo y no el contenido de la escena. Para detectar fotografías casi idénticas se usa una huella perceptual, un resumen binario de la imagen reducida. Dos huellas a pocos bits de distancia indican escenas muy parecidas.

**Preparación para redes convolucionales.** Las redes preentrenadas esperan una entrada de tamaño fijo y con la misma escala de valores que vieron al entrenarse. Por eso cada fotografía se redimensiona, se recorta al centro a 224 × 224 píxeles y se normaliza con la media y la desviación estándar de ImageNet. Durante el entrenamiento se aplican aumentos de datos: recortes aleatorios de escala y reflejos horizontales. Estos aumentos multiplican las vistas de cada fotografía sin cambiar su etiqueta y reducen el sobreajuste. En este problema no se alteran el tono ni la saturación, porque el color forma parte de la señal del daño.

### 3.2 Análisis de imágenes desde el punto de vista agrícola

El estrés hídrico se manifiesta en la planta con síntomas visibles: marchitamiento, enrollamiento de las hojas, amarillamiento y, en casos severos, secado de los tejidos. La FAO advierte que síntomas parecidos pueden deberse a otras causas, como enfermedades, deficiencias de nutrientes o la madurez del cultivo (Food and Agriculture Organization of the United Nations [FAO], s. f.). Una fotografía con hojas amarillas no permite atribuir por sí sola el daño a la sequía. Por eso el color se trata como una señal parcial y no como un diagnóstico.

Cho et al. (2024) organizan los métodos de evaluación del estrés hídrico según el sensor. Las cámaras térmicas miden la temperatura del dosel y las multiespectrales permiten calcular índices con bandas infrarrojas. Las cámaras RGB solo registran la apariencia visible. Las fotografías del proyecto son RGB y provienen de teléfonos inteligentes, así que los métodos fisiológicos de esa revisión no son reproducibles aquí.

El proyecto Eyes on the Ground recolectó fotografías de campos de pequeños productores en Kenia con teléfonos inteligentes. Su propósito fue apoyar un esquema de seguro agrícola basado en imágenes (Waithaka et al., 2022). En la competencia, la magnitud del daño es el porcentaje estimado de pérdida, en pasos de 10 de 0 a 100 (Zindi, 2023). Esta forma de captura introduce variaciones que no existen en estudios de laboratorio:

- **Encuadre y distancia:** cada fotografía muestra una porción distinta del campo, con cielo, suelo y vegetación en proporciones variables.
- **Iluminación:** la hora, las nubes y la dirección del sol cambian el color aparente de la planta.
- **Dispositivo:** la resolución y la calidad cambian entre teléfonos y entre temporadas.
- **Etapa fenológica:** un cultivo maduro se seca de forma natural y puede confundirse con daño por sequía.
- **Etiqueta:** la magnitud es una estimación visual de una persona, no una medición. Dos evaluadores pueden asignar valores distintos a la misma escena.

Estas condiciones explican por qué la literatura prefiere modelos que aprenden texturas y estructuras de la escena, en lugar de depender de un único índice de color.

### 3.3 Algoritmos de aprendizaje automático para el problema

#### Formulación como regresión

La magnitud es una variable numérica ordenada, por lo que el problema se plantea como regresión: el modelo devuelve un valor continuo entre 0 y 100. Las métricas adecuadas son el error absoluto medio (MAE), la raíz del error cuadrático medio (RMSE) y el coeficiente de determinación (R²). El MAE expresa el error típico en puntos de magnitud. El RMSE penaliza más los errores grandes. El R² compara el modelo con predecir siempre la media.

#### Modelos sobre atributos

Una estrategia clásica describe cada imagen con atributos de color, textura o forma y los usa como entradas de un modelo convencional. Cho et al. (2024) documentan el uso de máquinas de vectores de soporte, bosques aleatorios y redes neuronales con este enfoque. El bosque aleatorio combina muchos árboles de decisión, cada uno entrenado con una muestra distinta de los datos y de los atributos (Breiman, 2001). Promediar los árboles reduce la varianza de un árbol individual, y el método se aplica tanto a clasificación como a regresión. Su limitación en este problema es que los atributos globales pierden la estructura espacial: un promedio de color mezcla hojas, suelo y cielo.

#### Redes neuronales convolucionales

Una red convolucional aprende filtros que se deslizan sobre la imagen y detectan patrones locales. Las primeras capas responden a bordes y colores. Las capas profundas combinan esas respuestas en texturas, partes y objetos (LeCun et al., 2015). Al aprender la representación directamente de los píxeles, la red puede distinguir una hoja enrollada de una hoja sana con el mismo color medio.

#### Transferencia de aprendizaje

Entrenar una red profunda desde cero requiere cientos de miles de imágenes etiquetadas. La transferencia de aprendizaje parte de una red ya entrenada en un conjunto grande, normalmente ImageNet, con más de un millón de imágenes de mil categorías (Deng et al., 2009). Luego la adapta a la nueva tarea con pocos datos. Se puede reentrenar solo la capa de salida y conservar el resto como extractor de características, o ajustar también los últimos bloques. En agricultura es una práctica frecuente para reconocer enfermedades, malezas y estrés en plantas, porque los conjuntos etiquetados suelen ser pequeños (Kamilaris & Prenafeta-Boldú, 2018).

Mohanty et al. (2016) reconocieron 38 combinaciones de cultivo y enfermedad con una exactitud de 99.35 % dentro del conjunto PlantVillage. Sin embargo, en imágenes de otras fuentes la exactitud cayó a cerca de 31 %. El hallazgo muestra que un buen resultado en condiciones controladas no garantiza el desempeño en el campo. También muestra la importancia de evaluar con datos independientes: los autores agruparon las fotografías de una misma hoja para que no quedaran a ambos lados de la partición.

#### ResNet50

He et al. (2016) introdujeron las conexiones residuales. Cada bloque aprende una corrección que se suma a su propia entrada, de modo que el gradiente fluye sin degradarse aunque la red sea muy profunda. ResNet50 tiene 50 capas y alrededor de 25.6 millones de parámetros. Chandel et al. (2022) compararon cinco redes para identificar estrés hídrico en trigo con imágenes RGB y térmicas. Con imágenes RGB, ResNet50 obtuvo la mayor exactitud de validación, 96.9 %.

#### DenseNet121

Huang et al. (2017) propusieron la conectividad densa. Dentro de un bloque denso, cada capa recibe como entrada la concatenación de los mapas de características de todas las capas anteriores del bloque. Así, cada capa reutiliza lo que ya calcularon las demás y solo agrega unos pocos mapas nuevos, 32 por capa en DenseNet121. Entre bloques, unas capas de transición reducen el número de canales con convoluciones de 1 × 1 y la resolución con un promedio espacial.

DenseNet121 tiene cuatro bloques densos de 6, 12, 24 y 16 capas, y su salida es un vector de 1 024 características. Gracias a la reutilización, alcanza una exactitud comparable a ResNet50 en ImageNet con cerca de 8 millones de parámetros, menos de un tercio. Patra y Sahoo (2024) compararon cuatro redes preentrenadas para clasificar estrés hídrico en patata con imágenes RGB de dron, en condiciones de campo. DenseNet121 obtuvo la mayor exactitud de prueba, 90.75 %.

#### Adaptación a la estimación de severidad

Los estudios anteriores clasifican plantas como estresadas o sanas; ninguno estima una magnitud de 0 a 100 con fotografías como las del proyecto. Para adaptar las redes, se reemplaza la capa de clasificación por una neurona lineal que predice la magnitud dividida entre 100, y se entrena con el error cuadrático medio. La adaptación cambia la tarea aprendida, por lo que las exactitudes publicadas no son una expectativa del error de este proyecto.

La Tabla 3.1 resume la evidencia y su relación con el problema.

| Estudio | Aporte principal | Límite para el proyecto |
|:--|:--|:--|
| Cho et al. (2024) | Organiza sensores y familias de modelos para estrés hídrico. | Es una revisión; no ofrece experimentos con estos datos. |
| Chandel et al. (2021) | Compara AlexNet, GoogLeNet e Inception V3 en maíz, okra y soja. | Identifica estrés; no estima magnitud. |
| Chandel et al. (2022) | Compara cinco redes con imágenes RGB y térmicas de trigo. | Captura estandarizada y clasificación binaria. |
| Patra y Sahoo (2024) | Evalúa redes preentrenadas e interpretación visual en campo. | Clasifica regiones anotadas; no estima magnitud. |
| Mohanty et al. (2016) | Documenta la transferencia y la caída de desempeño externo. | Estudia enfermedades en hojas, no sequía en escenas completas. |
| Breiman (2001) | Fundamenta el bosque aleatorio y su uso en regresión. | No es evidencia experimental agrícola. |

: Tabla 3.1. Estudios consultados y su relación con el problema.

Con base en esta evidencia, el proyecto compara dos redes convolucionales preentrenadas, ResNet50 y DenseNet121, adaptadas a regresión. Como referencias se usan un bosque aleatorio y una regresión sobre el exceso de verde, que trabajan con atributos globales, y un predictor constante. Las referencias permiten medir cuánto aporta aprender la representación de la imagen frente a resumirla en pocos números.
