## 6. Resultados: ajuste y comparación de modelos

### 6.1 Protocolo de evaluación

Todos los modelos se entrenan con los registros de entrenamiento diagnosticados con sequía (DR): 3 655 fotografías de 1 453 campos. El conjunto de prueba agrupa el 20 % de los campos y contiene 4 628 registros, de los cuales 834 son DR. Los modelos solo estiman la severidad de la sequía. A los registros con otro diagnóstico se les asigna magnitud 0 mediante una regla fija, de modo que todos los modelos se evalúan sobre el mismo conjunto completo.

Se reportan dos alcances:

- **Alcance DR:** mide la tarea que aprenden los modelos sobre los 834 registros con sequía.
- **Alcance global:** incluye los 3 794 registros con otro diagnóstico. En ellos la regla acierta siempre, así que este alcance reduce el error de cualquier modelo.

Por eso la comparación se basa en el alcance DR. Las métricas son el error absoluto medio (MAE), la raíz del error cuadrático medio (RMSE) y el coeficiente de determinación (R²), todos sobre la escala de 0 a 100. El conjunto de prueba se usó una sola vez, después de fijar los hiperparámetros.

### 6.2 Predictor constante

El predictor constante asigna a cada fotografía DR la magnitud media del entrenamiento, 41.18. No tiene hiperparámetros. Sirve como referencia mínima: un modelo que no lo supera no aprende nada útil de la fotografía. En la prueba DR obtiene MAE de 19.78, RMSE de 24.09 y R² prácticamente nulo (−0.001), como corresponde a una predicción que no varía.

### 6.3 ResNet50

La ResNet50 parte de los pesos de ImageNet y reemplaza la capa de clasificación por una neurona lineal que predice la magnitud dividida entre 100. El procedimiento es el mismo que el de DenseNet121, para que las diferencias entre ambas redes reflejen la arquitectura y no la configuración.

La búsqueda probó dos tasas de aprendizaje y dos niveles de ajuste fino. Los niveles fueron entrenar solo la capa de salida (`cabeza`) o también el último bloque convolucional (`ultimo_bloque`). Cada configuración se entrenó con parada temprana sobre un pliegue de validación de 731 fotografías, cuyos campos no aparecen en las 2 924 de ajuste.

| Tasa de aprendizaje | Capas entrenadas | Mejor época | RMSE validación | MAE validación |
|:--|:--|--:|--:|--:|
| 3 × 10⁻⁴ | `ultimo_bloque` | 2 | **18.09** | **13.94** |
| 1 × 10⁻⁴ | `cabeza` | 13 | 18.34 | 14.34 |
| 3 × 10⁻⁴ | `cabeza` | 7 | 18.60 | 14.61 |
| 1 × 10⁻⁴ | `ultimo_bloque` | 7 | 18.82 | 14.37 |

Se eligió la configuración con menor RMSE de validación: tasa de 3 × 10⁻⁴, último bloque descongelado y 2 épocas. Con ella se reentrenó la red sobre las 3 655 fotografías DR de entrenamiento.

Las cuatro configuraciones quedan a menos de un punto de RMSE entre sí, así que el resultado depende poco de estos hiperparámetros. La curva de la configuración elegida muestra que la pérdida de validación alcanza su mínimo en la segunda época. Después sube, mientras la de entrenamiento sigue bajando. Al ajustar el último bloque, la red memoriza pronto las 2 924 fotografías de ajuste. Solo con la cabeza el aprendizaje es más lento (13 épocas) y llega a un error casi igual.

![Pérdida y MAE de validación por época de la configuración elegida de ResNet50.](figuras/06_curva_resnet.png)

El entrenamiento se hizo en una MacBook Pro con chip M5 Pro, usando la GPU mediante Metal (`mps`) y precisión mixta `bfloat16`. La búsqueda de cuatro configuraciones y el reentrenamiento final tardaron 11.4 minutos en total. La inferencia sobre la prueba DR promedió 13 ms por fotografía, incluida la lectura del archivo.

### 6.4 ResNet50 ajustada

La ResNet50 anterior sigue el procedimiento común de las redes convolucionales, para que su comparación con DenseNet121 refleje solo la arquitectura. Para saber cuánto mejora la misma arquitectura con otra receta de entrenamiento, se entrenó una segunda versión, la ResNet50 ajustada. Se registró como un modelo aparte, sin modificar la primera.

La receta se eligió con experimentos sobre el entrenamiento DR, sin usar la prueba. Primero se probaron siete cambios, uno a la vez, sobre el pliegue 0. La mayoría movió el RMSE de validación menos de un punto, dentro de la variación de la base entre una época y otra (de 18.1 a 19.7). Los cambios que redujeron el error se combinaron en una receta:

| Elemento | ResNet50 | ResNet50 ajustada |
|:--|:--|:--|
| Pesos iniciales | `IMAGENET1K_V1` | `IMAGENET1K_V2` |
| Capas entrenadas | Cabeza o último bloque | Toda la red |
| Tasa de aprendizaje | Una sola, 10⁻⁴ o 3 × 10⁻⁴ | 10⁻³ en la salida y 10⁻⁴ en el resto |
| Programa de la tasa | Constante | Coseno de 10 épocas |
| Selección de época | Parada temprana sobre validación | Última época |
| Tamaño de entrada | 224 | 320 |
| Predicción | Imagen centrada | Promedio de la imagen y su reflejo horizontal |

Los cambios descartados fueron la pérdida de Huber y descongelar solo los dos últimos bloques, que empeoraron el error, y los aumentos más agresivos, que no lo cambiaron.

La receta se fijó en el pliegue 0 y se evaluó en los pliegues 1 y 2 con la política fija, sin volver a elegir la época. Para la ResNet50 se usó la época 2, la que eligió su búsqueda:

| Pliegue | ResNet50, época 2 | ResNet50 ajustada, época 10 |
|:--|--:|--:|
| 0 | 18.09 | 18.02 |
| 1 | 19.23 | 17.16 |
| 2 | 21.43 | 18.55 |
| Media | 19.58 | 17.91 |

En el pliegue 0 ambas empatan, pero ahí la época de la ResNet50 se eligió con el mismo pliegue, lo que favorece su resultado. En los pliegues 1 y 2 la receta ajustada reduce el RMSE en 2 a 3 puntos.

La receta también es más estable. Con el programa coseno, la validación cambia poco en las últimas épocas, y no hace falta elegir una época sobre un pliegue ruidoso. La ResNet50, en cambio, varió hasta 5 puntos entre épocas en el pliegue 2.

El tamaño de entrada fue el cambio que más ayudó. Con la misma receta, la entrada de 320 tuvo menor RMSE de validación que la de 224 en casi todas las épocas: en promedio, 17.71 contra 18.40.

El cuaderno de entrenamiento repite esa elección sobre el pliegue 0 (18.02 con 320 y 18.36 con 224) y reentrena con las 3 655 fotografías DR durante 10 épocas.

![Pérdida y MAE de validación por época de la ResNet50 ajustada.](figuras/06b_curva_resnet_ajustada.png)

El tiempo de entrenamiento registrado es de 49.9 minutos. Ese valor incluye un tramo en que la computadora redujo su rendimiento por batería baja: algunas épocas tardaron hasta cuatro veces más que con el cargador conectado. Con el equipo conectado, el proceso completo tarda alrededor de 32 minutos. La inferencia promedia 29 ms por fotografía. Es más del doble que la ResNet50, por la entrada mayor y porque cada fotografía se procesa dos veces.

### 6.5 Comparación

| Modelo | MAE DR | RMSE DR | R² DR | MAE global | RMSE global | R² global | Entrenamiento (s) | Inferencia (ms) |
|:--|--:|--:|--:|--:|--:|--:|--:|--:|
| ResNet50 ajustada | **13.84** | **18.09** | **0.436** | **2.49** | **7.68** | **0.830** | 2 991 | 29.4 |
| ResNet50 | 15.03 | 18.81 | 0.390 | 2.71 | 7.98 | 0.816 | 683 | 13.0 |
| Predictor constante | 19.78 | 24.09 | −0.001 | 3.57 | 10.22 | 0.699 | < 0.001 | < 0.001 |

Las dos ResNet50 superan con claridad al predictor constante. La ResNet50 reduce el RMSE DR en 21.9 % y la ajustada, en 24.9 %. En ambas, el RMSE de prueba es cercano al de validación: 18.81 contra 18.09, y 18.09 contra 18.02. Esto indica que la partición por campo dio una estimación honesta del error.

Para saber si la diferencia entre las dos ResNet50 es real, se remuestrearon con reemplazo las 834 fotografías DR de prueba 5 000 veces (bootstrap pareado):

- **MAE:** la ajustada baja 1.19 puntos, con un intervalo de confianza al 95 % de −1.89 a −0.49. Como el intervalo no incluye el cero, la mejora es significativa.
- **RMSE:** la ajustada baja 0.71 puntos, con un intervalo de −1.58 a 0.15, y una probabilidad de mejora del 94.6 %.

La mejora en prueba es menor que la estimada con los pliegues de validación. Aun así, va en la misma dirección en todas las métricas y en las cuatro temporadas.

En el alcance global los errores bajan y el R² sube para todos los modelos, porque la regla acierta en los 3 794 registros con otro diagnóstico. Esa mejora no se debe al modelo y no debe leerse como capacidad para estimar la severidad.

![MAE y RMSE de cada modelo sobre la prueba, en los alcances DR y global.](figuras/07_comparacion_errores.png)

La gráfica de magnitud real contra predicha muestra la principal limitación de las redes: comprimen sus predicciones hacia el centro de la escala. Sobrestiman los daños leves y subestiman los severos:

| Magnitud real | 10 | 40 | 60 | 90 | 100 |
|:--|--:|--:|--:|--:|--:|
| Predicción media, ResNet50 | 32.4 | 45.1 | 57.3 | 67.4 | 72.6 |
| Predicción media, ResNet50 ajustada | 25.5 | 40.1 | 55.1 | 68.9 | 63.9 |

La ajustada corrige buena parte del sesgo en los daños leves, que son los más frecuentes, pero no en los severos. Con solo 9 fotografías de magnitud 100 en la prueba, la media de ese nivel es poco estable.

La predicción media crece con la magnitud real, así que ambas redes ordenan bien las fotografías por severidad aunque no acierten el valor exacto. Las predicciones DR que quedan cerca del valor real son:

| Distancia al valor real | ResNet50 | ResNet50 ajustada |
|:--|--:|--:|
| 10 puntos o menos | 40.5 % | 47.5 % |
| 20 puntos o menos | 71.8 % | 76.6 % |

![Magnitud real contra predicha en los registros DR de prueba.](figuras/07_real_vs_predicho.png)

Las dos redes mejoran al predictor constante en las cuatro temporadas. La ganancia mayor se da en SR2020, donde el RMSE baja de 30.04 a cerca de 20.6. En esa temporada las magnitudes se alejan más de la media general, por lo que el predictor constante falla más.

La ajustada tiene menor RMSE que la ResNet50 en las cuatro temporadas. Su RMSE por temporada va de 15.64 (LR2020) a 20.61 (SR2020). SR2020 es la temporada más difícil para ambas redes, lo que sugiere que sus condiciones de captura influyen en el error.

![RMSE por temporada en los registros DR de prueba.](figuras/07_error_por_temporada.png)

En tiempos, el predictor constante es instantáneo. La ResNet50 requiere 683 segundos de entrenamiento y 13 ms por fotografía en la GPU de la Mac. La ajustada, unos 32 minutos con el equipo conectado y 29 ms por fotografía. Ambos costos de inferencia son compatibles con la aplicación, que responde a cada fotografía en línea. Los modelos del equipo se entrenaron en computadoras distintas, por lo que los tiempos solo son comparables en orden de magnitud.

![Tiempo de entrenamiento y de inferencia por modelo, en escala logarítmica.](figuras/07_tiempos.png)

El criterio de selección del cuaderno de comparación usa el RMSE DR. Si dos modelos quedan a menos de un punto, prefiere el de menor tiempo de inferencia. Las dos ResNet50 quedan a 0.7 puntos, así que el criterio recomienda la ResNet50 del procedimiento común, que es más del doble de rápida. Si la latencia no es una restricción, la ResNet50 ajustada es la de menor error en todas las métricas, y su ventaja en MAE es significativa.

Esta comparación incluye los modelos con resultados disponibles al generar el informe. La regresión sobre exceso de verde, Random Forest y DenseNet121 se agregan al ejecutar de nuevo el cuaderno `07_comparacion_modelos.ipynb`. El cuaderno lee todos los resultados guardados y aplica el mismo criterio de selección.
