## 6. Resultados: ajuste y comparación de modelos

### 6.1 Protocolo de evaluación

Todos los modelos se entrenan con los registros de entrenamiento diagnosticados con sequía (DR): 3 655 fotografías de 1 453 campos. El conjunto de prueba agrupa el 20 % de los campos y contiene 4 628 registros, de los cuales 834 son DR. Los modelos solo estiman la severidad de la sequía. A los registros con otro diagnóstico se les asigna magnitud 0 mediante una regla fija, de modo que todos los modelos se evalúan sobre el mismo conjunto completo.

Se reportan dos alcances:

- **Alcance DR:** mide la tarea que aprenden los modelos sobre los 834 registros con sequía.
- **Alcance global:** incluye los 3 794 registros con otro diagnóstico. En ellos la regla acierta siempre, así que este alcance reduce el error de cualquier modelo.

Por eso la comparación se basa en el alcance DR. Las métricas son el error absoluto medio (MAE), la raíz del error cuadrático medio (RMSE) y el coeficiente de determinación (R²), todos sobre la escala de 0 a 100. El conjunto de prueba se usó una sola vez por modelo, después de fijar los hiperparámetros. Los seis modelos se entrenaron en el mismo equipo (sección 4.5), así que sus tiempos son comparables entre sí.

### 6.2 Predictor constante

El predictor constante asigna a cada fotografía DR la magnitud media del entrenamiento, 41.18. No tiene hiperparámetros. Sirve como referencia mínima: un modelo que no lo supera no aprende nada útil de la fotografía. En la prueba DR obtiene MAE de 19.78, RMSE de 24.09 y R² prácticamente nulo (−0.001), como corresponde a una predicción que no varía.

### 6.3 Regresión lineal sobre el exceso de verde

La regresión usa un único atributo, el exceso de verde, que fue el de mayor correlación con la magnitud en el análisis exploratorio. No tiene hiperparámetros. El modelo ajustado es:

$$\widehat{\text{magnitud}} = 54.46 - 146.79 \cdot ExG$$

La pendiente negativa es coherente con la pérdida de verdor que causa la sequía: un aumento de 0.1 en el exceso de verde reduce la magnitud estimada en unos 14.7 puntos. En la prueba DR obtiene MAE de 17.64, RMSE de 21.44 y R² de 0.207. Mejora al predictor constante en 2.6 puntos de RMSE, pero sus predicciones varían poco: la media va de 35.8 para las fotografías con magnitud real 10 a 54.1 para las de magnitud 100.

### 6.4 Random Forest

El Random Forest usa nueve atributos globales: exceso de verde, saturación, brillo, contraste, las tres medias de canal y las dos proporciones de exposición. La búsqueda probó 30 combinaciones de hiperparámetros con validación cruzada de cinco pliegues agrupados por campo. Las cuatro mejores fueron:

| Árboles | Hoja mínima | Atributos por división | Profundidad máxima | RMSE validación | MAE validación |
|--:|--:|:--|:--|--:|--:|
| 200 | 10 | raíz cuadrada | 10 | **20.65** | 16.43 |
| 300 | 20 | 0.5 | sin límite | 20.67 | 16.43 |
| 100 | 20 | 0.5 | 20 | 20.67 | 16.44 |
| 200 | 10 | 0.5 | 10 | 20.68 | **16.41** |

: Tabla 6.1. Mejores combinaciones de la búsqueda del Random Forest.

Las 30 combinaciones quedan entre 20.65 y 21.04 de RMSE de validación, así que el error depende poco de los hiperparámetros. Entre las mejores predominan hojas de 10 a 20 registros, que suavizan las predicciones. Las peores limitan la profundidad a 5 o combinan hojas de un solo registro con todos los atributos. La combinación elegida se reajustó con todo el entrenamiento DR.

**Atributos del dispositivo.** El análisis exploratorio mostró que los megapíxeles y la nitidez cambian con la temporada y pueden describir el teléfono más que el daño. Agregarlos baja el RMSE de validación de 20.65 a 20.39, una mejora menor que la diferencia entre combinaciones de la búsqueda. Como la validación mezcla las cuatro temporadas, no permite saber si esa ganancia viene del daño o de reconocer la temporada por el teléfono. Por eso el modelo final los excluye.

**Importancia de los atributos.** El exceso de verde concentra 0.47 de la importancia, casi cuatro veces más que el siguiente atributo, la media del canal rojo (0.12). El resultado coincide con el análisis exploratorio y confirma que ese índice resume buena parte de la señal de color de la sequía.

![Importancia de los atributos en el Random Forest.](figuras/04_importancia_atributos.png)

**Generalización temporal.** Dentro del entrenamiento DR, se entrenó el Random Forest con LR2020, SR2020 y LR2021 y se evaluó en SR2021. Obtuvo un RMSE de 20.53, muy cercano al 20.65 de la validación por campo, mientras que predecir la media de las temporadas anteriores llega a 24.19. No se observa una caída al cambiar de temporada. El resultado es en parte optimista: 353 de los 732 campos de SR2021 también aparecen en las temporadas anteriores y concentran el 53 % de sus registros.

En la prueba DR, el Random Forest obtiene MAE de 16.68, RMSE de 20.61 y R² de 0.267. La búsqueda completa y el reajuste tardaron 23 segundos en la CPU, y la inferencia es de 0.02 ms por registro, porque parte de los atributos ya calculados.

### 6.5 ResNet50

La ResNet50 parte de los pesos de ImageNet y reemplaza la capa de clasificación por una neurona lineal que predice la magnitud dividida entre 100. El procedimiento es el mismo que el de DenseNet121, para que las diferencias entre ambas redes reflejen la arquitectura y no la configuración.

La búsqueda probó dos tasas de aprendizaje y dos niveles de ajuste fino. Los niveles fueron entrenar solo la capa de salida (`cabeza`) o también el último bloque convolucional (`ultimo_bloque`). Cada configuración se entrenó con parada temprana sobre un pliegue de validación de 731 fotografías, cuyos campos no aparecen en las 2 924 de ajuste.

| Tasa de aprendizaje | Capas entrenadas | Mejor época | RMSE validación | MAE validación |
|:--|:--|--:|--:|--:|
| 3 × 10⁻⁴ | `ultimo_bloque` | 2 | **17.99** | **13.85** |
| 1 × 10⁻⁴ | `cabeza` | 13 | 18.34 | 14.33 |
| 3 × 10⁻⁴ | `cabeza` | 7 | 18.59 | 14.60 |
| 1 × 10⁻⁴ | `ultimo_bloque` | 7 | 18.74 | 14.52 |

: Tabla 6.2. Configuraciones probadas para ResNet50.

Se eligió la configuración con menor RMSE de validación: tasa de 3 × 10⁻⁴, último bloque descongelado y 2 épocas. Con ella se reentrenó la red sobre las 3 655 fotografías DR de entrenamiento.

Las cuatro configuraciones quedan a menos de un punto de RMSE entre sí, así que el resultado depende poco de estos hiperparámetros. La curva de la configuración elegida muestra que la pérdida de validación alcanza su mínimo en la segunda época. Después sube, mientras la de entrenamiento sigue bajando: al ajustar el último bloque, la red memoriza pronto las fotografías de ajuste. Solo con la cabeza el aprendizaje es más lento (13 épocas) y llega a un error casi igual.

![Pérdida y MAE de validación por época de la configuración elegida de ResNet50.](figuras/06_curva_resnet.png)

En la prueba DR obtiene MAE de 14.61, RMSE de 18.33 y R² de 0.420. La búsqueda de cuatro configuraciones y el reentrenamiento final tardaron 10.3 minutos, y la inferencia promedió 20.3 ms por fotografía, incluida la lectura del archivo.

### 6.6 ResNet50 ajustada

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

: Tabla 6.3. Receta de la ResNet50 frente a la ResNet50 ajustada.

Los cambios descartados fueron la pérdida de Huber y descongelar solo los dos últimos bloques, que empeoraron el error, y los aumentos más agresivos, que no lo cambiaron.

La receta se fijó en el pliegue 0 y se evaluó en los pliegues 1 y 2 con la política fija, sin volver a elegir la época. Para la ResNet50 se usó la época 2, la que eligió su búsqueda. Estos experimentos de selección se hicieron en la etapa de diseño de la receta:

| Pliegue | ResNet50, época 2 | ResNet50 ajustada, época 10 |
|:--|--:|--:|
| 0 | 18.09 | 18.02 |
| 1 | 19.23 | 17.16 |
| 2 | 21.43 | 18.55 |
| Media | 19.58 | 17.91 |

: Tabla 6.4. RMSE de validación por pliegue durante la selección de la receta.

En el pliegue 0 ambas empatan, pero ahí la época de la ResNet50 se eligió con el mismo pliegue, lo que favorece su resultado. En los pliegues 1 y 2 la receta ajustada reduce el RMSE en 2 a 3 puntos. La receta también es más estable: con el programa coseno, la validación cambia poco en las últimas épocas y no hace falta elegir una época sobre un pliegue ruidoso.

El tamaño de entrada fue el cambio que más ayudó. El cuaderno de entrenamiento repite esa elección sobre el pliegue 0: la entrada de 320 obtiene un RMSE de validación de 17.43, frente a 18.39 con 224. Después reentrena con las 3 655 fotografías DR durante 10 épocas.

![Pérdida y MAE de validación por época de la ResNet50 ajustada.](figuras/06b_curva_resnet_ajustada.png)

En la prueba DR obtiene MAE de 13.50, RMSE de 17.84 y R² de 0.451. El proceso completo tardó 17.0 minutos y la inferencia promedia 30.8 ms por fotografía. Es la red más lenta, por la entrada mayor y porque cada fotografía se procesa dos veces.

### 6.7 DenseNet121

DenseNet121 sigue el mismo procedimiento común que la ResNet50. En esta red, `cabeza` entrena solo la capa lineal de salida y `ultimo_bloque` entrena además el cuarto bloque denso y la normalización final.

| Tasa de aprendizaje | Capas entrenadas | Mejor época | RMSE validación | MAE validación |
|:--|:--|--:|--:|--:|
| 3 × 10⁻⁴ | `cabeza` | 14 | **18.92** | **14.89** |
| 1 × 10⁻⁴ | `ultimo_bloque` | 11 | 19.26 | 15.18 |
| 1 × 10⁻⁴ | `cabeza` | 15 | 19.82 | 15.62 |
| 3 × 10⁻⁴ | `ultimo_bloque` | 2 | 20.92 | 16.34 |

: Tabla 6.5. Configuraciones probadas para DenseNet121.

Se eligió la tasa de 3 × 10⁻⁴ entrenando solo la cabeza, durante 14 épocas. A diferencia de la ResNet50, la mejor configuración no ajusta el último bloque. Con la tasa mayor, ajustar el cuarto bloque denso sobreajustó desde la segunda época y dio el peor resultado. Con la tasa menor, en cambio, el último bloque mejoró a la cabeza sola. La cabeza sola aprende despacio: con 10⁻⁴ seguía mejorando en la época 15, el máximo permitido.

La curva de la configuración elegida baja de forma sostenida y casi sin separación entre entrenamiento y validación. Con los bloques congelados, la red no memoriza las fotografías de ajuste, pero tampoco adapta sus filtros a las señales de la sequía.

![Pérdida y MAE de validación por época de la configuración elegida de DenseNet121.](figuras/05_curva_densenet.png)

En la prueba DR obtiene MAE de 15.58, RMSE de 19.36 y R² de 0.354. La búsqueda y el reentrenamiento tardaron 14.2 minutos, y la inferencia promedia 24.4 ms por fotografía.

### 6.8 Comparación

| Modelo | MAE DR | RMSE DR | R² DR | MAE global | RMSE global | R² global | Entrenamiento (s) | Inferencia (ms) |
|:--|--:|--:|--:|--:|--:|--:|--:|--:|
| ResNet50 ajustada | **13.50** | **17.84** | **0.451** | **2.43** | **7.57** | **0.835** | 1 021 | 30.8 |
| ResNet50 | 14.61 | 18.33 | 0.420 | 2.63 | 7.78 | 0.826 | 620 | 20.3 |
| DenseNet121 | 15.58 | 19.36 | 0.354 | 2.81 | 8.22 | 0.806 | 850 | 24.4 |
| Random Forest | 16.68 | 20.61 | 0.267 | 3.01 | 8.75 | 0.780 | 23 | 0.02 |
| Regresión sobre exceso de verde | 17.64 | 21.44 | 0.207 | 3.18 | 9.10 | 0.762 | 0.06 | < 0.01 |
| Predictor constante | 19.78 | 24.09 | −0.001 | 3.57 | 10.22 | 0.699 | < 0.001 | < 0.001 |

: Tabla 6.6. Métricas de prueba y tiempos de los seis modelos.

Los cinco modelos superan al predictor constante, y el orden es claro: las redes convolucionales mejoran más que los modelos sobre atributos globales. El Random Forest reduce el RMSE DR en 14.4 % respecto del predictor constante; DenseNet121, en 19.6 %; la ResNet50, en 23.9 %, y la ResNet50 ajustada, en 25.9 %. El salto entre el Random Forest y la mejor red, casi tres puntos de RMSE, muestra que la textura y la estructura de la escena aportan información que los promedios de color no capturan.

En todos los modelos el RMSE de prueba es cercano al de validación: 20.61 contra 20.65 en el Random Forest, 18.33 contra 17.99 en la ResNet50, 17.84 contra 17.43 en la ajustada y 19.36 contra 18.92 en DenseNet121. Esto indica que la partición por campo dio una estimación honesta del error.

![MAE y RMSE de cada modelo sobre la prueba, en los alcances DR y global.](figuras/07_comparacion_errores.png)

**Arquitectura.** Con el mismo procedimiento, la ResNet50 supera a DenseNet121 por un punto de RMSE. Para saber si la diferencia es real, se remuestrearon con reemplazo las 834 fotografías DR de prueba 5 000 veces (bootstrap pareado). La ResNet50 baja el RMSE en 1.02 puntos, con un intervalo de confianza al 95 % de −1.65 a −0.38, y el MAE en 0.97 puntos (de −1.54 a −0.40). Ningún intervalo incluye el cero, así que en este problema la ResNet50 es la mejor arquitectura de las dos. Una explicación probable es que DenseNet121 eligió no ajustar sus bloques, mientras que la ResNet50 sí adaptó su último bloque.

**Receta.** El mismo bootstrap compara las dos ResNet50:

- **MAE:** la ajustada baja 1.11 puntos, con un intervalo de −1.81 a −0.42. Como el intervalo no incluye el cero, la mejora es significativa.
- **RMSE:** la ajustada baja 0.49 puntos, con un intervalo de −1.33 a 0.38 y una probabilidad de mejora del 86.9 %.

En el alcance global los errores bajan y el R² sube para todos los modelos, porque la regla acierta en los 3 794 registros con otro diagnóstico. Esa mejora no se debe al modelo y no debe leerse como capacidad para estimar la severidad.

**Compresión hacia el centro.** La gráfica de magnitud real contra predicha muestra la principal limitación de todos los modelos: comprimen sus predicciones hacia el centro de la escala. Sobrestiman los daños leves y subestiman los severos:

| Magnitud real | 10 | 40 | 60 | 90 | 100 |
|:--|--:|--:|--:|--:|--:|
| Random Forest | 34.2 | 40.7 | 48.6 | 55.3 | 55.2 |
| DenseNet121 | 30.4 | 42.8 | 56.3 | 61.9 | 67.2 |
| ResNet50 | 31.1 | 43.7 | 55.5 | 65.7 | 69.7 |
| ResNet50 ajustada | 25.8 | 39.2 | 53.4 | 68.3 | 62.9 |

: Tabla 6.7. Predicción media por nivel de magnitud real en la prueba DR.

Los modelos sobre atributos casi no distinguen los daños severos: el Random Forest predice cerca de 55 para todas las fotografías con magnitud 80 o más. Las redes abren más la escala. La ajustada corrige buena parte del sesgo en los daños leves, que son los más frecuentes. Con solo 9 fotografías de magnitud 100 en la prueba, la media de ese nivel es poco estable.

La predicción media crece con la magnitud real, así que las redes ordenan bien las fotografías por severidad aunque no acierten el valor exacto. Las predicciones DR que quedan cerca del valor real son:

| Distancia al valor real | Random Forest | DenseNet121 | ResNet50 | ResNet50 ajustada |
|:--|--:|--:|--:|--:|
| 10 puntos o menos | 35.5 % | 39.0 % | 41.8 % | 48.3 % |
| 20 puntos o menos | 65.8 % | 68.6 % | 73.4 % | 77.3 % |

: Tabla 6.8. Proporción de predicciones DR cercanas al valor real.

![Magnitud real contra predicha en los registros DR de prueba.](figuras/07_real_vs_predicho.png)

**Temporadas.** Todos los modelos mejoran al predictor constante en las cuatro temporadas. La ganancia mayor se da en SR2020, donde el RMSE baja de 30.04 a 20.10 con la ResNet50 ajustada. En esa temporada las magnitudes se alejan más de la media general, por lo que el predictor constante falla más. SR2020 sigue siendo la temporada más difícil para todos los modelos, lo que sugiere que sus condiciones de captura influyen en el error. La ResNet50 ajustada tiene el menor RMSE en las cuatro temporadas, de 15.52 en LR2020 a 20.10 en SR2020.

![RMSE por temporada en los registros DR de prueba.](figuras/07_error_por_temporada.png)

**Tiempos.** Los modelos sobre atributos se entrenan en segundos y predicen en centésimas de milisegundo, sin contar la extracción de atributos. Las redes requieren de 10 a 17 minutos de entrenamiento en la GPU y de 20 a 31 ms por fotografía. Todos los costos de inferencia son compatibles con la aplicación, que responde a cada fotografía en línea.

![Tiempo de entrenamiento y de inferencia por modelo, en escala logarítmica.](figuras/07_tiempos.png)

**Recomendación.** El criterio de selección usa el RMSE DR. Si dos modelos quedan a menos de un punto, prefiere el de menor tiempo de inferencia. Las dos ResNet50 quedan a 0.49 puntos, así que el criterio recomienda la ResNet50 del procedimiento común, que predice en dos tercios del tiempo. Si la latencia no es una restricción, la ResNet50 ajustada es la de menor error en todas las métricas, y su ventaja en MAE es significativa.
