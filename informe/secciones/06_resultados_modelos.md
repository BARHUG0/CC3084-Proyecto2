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

### 6.4 Comparación

| Modelo | MAE DR | RMSE DR | R² DR | MAE global | RMSE global | R² global | Entrenamiento (s) | Inferencia (ms) |
|:--|--:|--:|--:|--:|--:|--:|--:|--:|
| ResNet50 | **15.03** | **18.81** | **0.390** | **2.71** | **7.98** | **0.816** | 683 | 13.0 |
| Predictor constante | 19.78 | 24.09 | −0.001 | 3.57 | 10.22 | 0.699 | < 0.001 | < 0.001 |

La ResNet50 reduce el RMSE DR del predictor constante en 21.9 % y el MAE en casi 5 puntos. El RMSE de prueba (18.81) es cercano al de validación (18.09). Esto indica que la partición por campo dio una estimación honesta del error y que el modelo no se sobreajustó a la validación.

En el alcance global los errores bajan y el R² sube para ambos modelos, porque la regla acierta en los 3 794 registros con otro diagnóstico. Esa mejora no se debe al modelo y no debe leerse como capacidad para estimar la severidad.

![MAE y RMSE de cada modelo sobre la prueba, en los alcances DR y global.](figuras/07_comparacion_errores.png)

La gráfica de magnitud real contra predicha muestra la principal limitación de la red: comprime sus predicciones hacia el centro de la escala. Sobrestima los daños leves y subestima los severos:

| Magnitud real | 10 | 40 | 60 | 100 |
|:--|--:|--:|--:|--:|
| Predicción media | 32.4 | 45.1 | 57.3 | 72.6 |

La predicción media crece con la magnitud real, así que la red ordena bien las fotografías por severidad aunque no acierte el valor exacto. El 40.5 % de las predicciones DR queda a 10 puntos o menos del valor real y el 71.8 %, a 20 puntos o menos.

![Magnitud real contra predicha en los registros DR de prueba.](figuras/07_real_vs_predicho.png)

La ResNet50 mejora al predictor constante en las cuatro temporadas. La ganancia mayor se da en SR2020, donde el RMSE baja de 30.04 a 20.70. En esa temporada las magnitudes se alejan más de la media general, por lo que el predictor constante falla más. Por temporada, el RMSE de la red va de 17.20 (LR2020) a 20.70 (SR2020). Esa diferencia moderada sugiere que las condiciones de captura de cada temporada influyen en el error, pero no lo determinan.

![RMSE por temporada en los registros DR de prueba.](figuras/07_error_por_temporada.png)

En tiempos, el predictor constante es instantáneo. La ResNet50 requiere 683 segundos de entrenamiento y 13 ms por fotografía en la GPU de la Mac. Ese costo de inferencia es compatible con la aplicación, que responde a cada fotografía en línea. Los modelos del equipo se entrenaron en computadoras distintas, por lo que los tiempos solo son comparables en orden de magnitud.

![Tiempo de entrenamiento y de inferencia por modelo, en escala logarítmica.](figuras/07_tiempos.png)

Esta comparación incluye los modelos con resultados disponibles al generar el informe. La regresión sobre exceso de verde, Random Forest y DenseNet121 se agregan al ejecutar de nuevo el cuaderno `07_comparacion_modelos.ipynb`. El cuaderno lee todos los resultados guardados y aplica el mismo criterio de selección.
