## 2. Objetivos

### Objetivo general

Estimar la magnitud del daño por sequía, en la escala de 0 a 100, a partir de fotografías de cultivos tomadas por pequeños productores. Para ello se comparan modelos basados en atributos visuales globales con redes convolucionales preentrenadas, y el resultado se pone a disposición en una aplicación web.

### Objetivos específicos

1. **Obtención y preparación de los datos.** Construir un flujo reproducible de descarga, verificación, limpieza y extracción de atributos. El flujo produce un conjunto de modelado con una partición fija entre entrenamiento y prueba, en la que ningún campo aparece en ambos lados.
2. **Análisis de los datos.** Cuantificar la proporción de cada diagnóstico, la distribución de la magnitud y las diferencias en las condiciones de captura entre temporadas, para definir el alcance del modelado y de la evaluación.
3. **Construcción y comparación de modelos.** Entrenar un predictor constante de referencia, una regresión lineal sobre el exceso de verde, un Random Forest y dos redes convolucionales, DenseNet121 y ResNet50. Compararlos por MAE, RMSE y R² sobre las fotografías con sequía del conjunto de prueba.
4. **Ajuste de hiperparámetros.** Seleccionar los hiperparámetros de cada algoritmo con validación agrupada por campo, registrando el error de validación de cada configuración probada.
5. **Costo computacional.** Medir el tiempo de entrenamiento de cada modelo y su tiempo de inferencia por fotografía.
6. **Aplicación.** Desarrollar una API y una interfaz web que permitan consultar los datos, comparar los modelos y estimar la magnitud de una fotografía nueva.
