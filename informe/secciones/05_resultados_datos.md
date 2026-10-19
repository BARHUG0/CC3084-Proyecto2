## 5. Resultados: datos, limpieza y análisis exploratorio

### 5.1 Características del conjunto original

Los datos provienen de la competencia CGIAR Eyes on the Ground, publicada en Zindi (2023). La tabla de registros (`Train.csv`, `Test.csv` y `SampleSubmission.csv`) se descargó desde la API de Zindi y las fotografías, desde la carpeta compartida indicada en el repositorio. Las imágenes se organizaron en las particiones `train` y `test`, y el cuaderno `01_adquisicion_datos.ipynb` verificó que cada registro tuviera su archivo y viceversa.

| Conjunto | Registros | Imágenes en disco | Correspondencia |
|:--|--:|--:|:--|
| Entrenamiento | 26 068 | 26 068 | Sin registros huérfanos ni imágenes sin registro |
| Prueba | 8 663 | 8 663 | Sin registros huérfanos ni imágenes sin registro |
| Total | 34 731 | 34 731 | Correspondencia completa |

: Tabla 5.1. Volumen y correspondencia por conjunto.

El conteo de entrenamiento quedó 38 registros por debajo del conteo oficial de 26 106: falta 1 registro en LR2020, 34 en LR2021 y 3 en SR2021. Como la correspondencia entre la tabla y los archivos locales es exacta, la diferencia está en el conjunto distribuido y no en la descarga. La partición de prueba de Zindi no incluye la magnitud real, por lo que solo sirve para describir las imágenes y no para evaluar modelos.

Cada registro tiene seis variables originales:

| Variable | Tipo | Descripción |
|:--|:--|:--|
| `ID` | Texto | Identificador del registro. |
| `filename` | Texto | Nombre del archivo de la fotografía. |
| `growth_stage` | Categórica ordinal | Etapa de crecimiento: siembra (S), vegetativa (V), floración (F) o madurez (M). |
| `damage` | Categórica nominal | Tipo de daño: sano (G), sequía (DR), enfermedad (DS), inundación (FD), deficiencia de nutrientes (ND), plaga (PS), maleza (WD) o viento (WN). |
| `extent` | Entera | Magnitud del daño, de 0 a 100 en pasos de 10. Es la variable objetivo. |
| `season` | Categórica ordinal | Temporada: LR2020, SR2020, LR2021 o SR2021. |

: Tabla 5.2. Variables originales del conjunto.

Las variables se renombraron al español (`etapa`, `dano`, `magnitud` y `temporada`). Del nombre del archivo se derivaron el productor, el campo, el cultivo, el sitio y el tipo de captura: inicial, de seguimiento o de reclamo. El formato codificado del nombre permite separar todos esos elementos. En el formato secuencial no se distinguen campos, así que el productor se usa como aproximación del campo. En 2 712 registros el formato no se reconoce y no aporta campo ni tipo de captura.

### 5.2 Limpieza

La limpieza conservó los registros y agregó indicadores de calidad, en lugar de imputar o eliminar información sin una justificación empírica. El entrenamiento no tuvo faltantes en las variables originales, identificadores duplicados ni valores fuera de dominio. Los faltantes se concentraron en las variables derivadas del nombre de archivo.

| Verificación | Registros | Decisión |
|:--|--:|:--|
| Formato de nombre desconocido | 2 712 | Se conservaron y se excluyeron de los cruces que dependen del formato. |
| Campo o productor no identificado | 2 712 | Se excluyeron del modelado, porque no pueden asignarse a un grupo de la partición. |
| Cultivo o sitio no identificado | 4 745 | Se conservaron sin imputación. |
| Magnitud fuera de dominio | 0 | No se requirió corrección. |
| Identificador o archivo duplicado | 0 | No se eliminó ningún registro. |
| Sequía con magnitud cero | 6 | Se conservaron como posible ruido de etiqueta. |
| Magnitud positiva con daño distinto de sequía | 0 | No se observó esta incoherencia. |

: Tabla 5.3. Bitácora de limpieza y decisiones.

El indicador `apto_modelado` marca 23 356 registros de entrenamiento con campo identificado. Las 34 731 fotografías se leyeron sin errores, y ninguna conservó los metadatos EXIF de marca y modelo del teléfono. Por eso el análisis se basa solo en los píxeles.

### 5.3 Preprocesamiento

**Atributos de imagen.** El módulo `src.caracteristicas` recorre las fotografías en paralelo y guarda los atributos en una caché de Parquet. Cada imagen se reduce a una miniatura de 256 píxeles por lado antes de calcular los atributos fotométricos. Se obtienen el exceso de verde, la saturación, el brillo, el contraste, las medias por canal, la nitidez, las proporciones de píxeles sobreexpuestos y subexpuestos, los megapíxeles, la relación de aspecto y la huella perceptual.

**Conjunto de modelado.** El módulo `src.conjunto` une los metadatos aptos para modelado con los atributos de imagen y produce un único archivo, `conjunto_modelado.parquet`, con 23 356 registros de 3 051 campos. De ellos, 4 495 tienen diagnóstico de sequía.

**Partición por campo.** Las fotografías de un mismo campo se parecen entre sí, así que separarlas al azar dejaría escenas casi iguales en el entrenamiento y en la prueba. Para evitarlo, la partición asigna campos completos: el 20 % de los campos va a la prueba con `GroupShuffleSplit` y una semilla fija (42). Todo el equipo obtiene la misma partición. Dentro del entrenamiento, la validación usa `GroupKFold` con cinco pliegues, también agrupados por campo.

| Subconjunto | Registros | Registros DR | Campos |
|:--|--:|--:|--:|
| Entrenamiento | 18 726 | 3 659 | 2 440 |
| Prueba | 4 630 | 836 | 611 |

: Tabla 5.4. Partición del conjunto de modelado por campo.

**Preparación para las redes.** Las redes convolucionales reciben la fotografía completa. Las fotografías grandes se decodifican directamente a una escala reducida, sin bajar de 512 píxeles por lado, porque algunas de SR2021 superan los 10 megapíxeles y leerlas completas haría lento el entrenamiento. Después se redimensiona a 256 píxeles, se recorta al centro a 224 × 224 y se normaliza con las estadísticas de ImageNet. La aplicación aplica la misma transformación a cada fotografía que recibe, sin que el usuario intervenga.

### 5.4 Análisis exploratorio

#### Magnitud y diagnóstico de sequía

La magnitud tiene media de 7.10, desviación estándar de 18.61 y mediana de 0. El 82.70 % de los registros de entrenamiento tiene magnitud cero. Con el criterio intercuartílico, los 4 510 valores positivos aparecerían como atípicos, porque el primer y el tercer cuartil valen cero. Esa marca no se usó para depurar: los valores positivos son precisamente el fenómeno de interés.

![Distribución de la magnitud en el entrenamiento.](figuras/02_histograma_magnitud.png)

La magnitud positiva aparece solo en los registros con diagnóstico de sequía (DR). Los otros siete tipos de daño tienen siempre magnitud cero.

| Daño | Registros | Media de magnitud | Máximo |
|:--|--:|--:|--:|
| Sano (G) | 11 623 | 0.00 | 0 |
| Sequía (DR) | 4 516 | 40.96 | 100 |
| Maleza (WD) | 9 238 | 0.00 | 0 |
| Otros cinco tipos | 691 | 0.00 | 0 |

: Tabla 5.5. Magnitud por tipo de daño en el entrenamiento.

Este hallazgo divide el problema en dos partes: reconocer la sequía y estimar su severidad. Como el diagnóstico está disponible en los datos y en la aplicación, los modelos estiman la severidad solo dentro de DR. A los demás diagnósticos se les asigna magnitud cero mediante una regla.

#### Severidad por temporada y etapa

Dentro de DR, la magnitud tiene media de 40.96 y mediana de 40, pero cambia entre temporadas. SR2020 registra una media de 53.52; LR2020, de 43.15; SR2021, de 37.06, y LR2021, de 34.50. Un modelo entrenado con una mezcla de temporadas debe estimar severidades que no se distribuyen igual en cada una.

![Magnitud de la sequía por temporada.](figuras/02_caja_magnitud_sequia_temporada.png)

La sequía se concentra en la madurez: el 48.59 % de los registros en etapa M tiene diagnóstico DR, frente a 13.82 % en F, 4.05 % en V y 0.62 % en S. La asociación sugiere que la etapa influye en la visibilidad o en la anotación del daño, sin demostrar una relación causal.

![Composición del tipo de daño por etapa.](figuras/02_apiladas_etapa_dano.png)

#### Asociación entre variables

La V de Cramér más alta se observa entre el daño y la etapa (0.32), seguida por la temporada y el tipo de captura (0.23). El eta cuadrado indica que el daño explica el 69.37 % de la varianza de la magnitud y la etapa, el 19.91 %. La temporada solo explica el 0.84 % en el conjunto completo, porque la gran cantidad de ceros oculta las diferencias que sí aparecen dentro de DR.

![Asociación entre variables categóricas mediante la V de Cramér.](figuras/02_mapa_cramers.png)

#### Agrupación por campo

Se identificaron 3 051 campos a partir de los nombres reconocidos. La mediana es de 6 fotografías por campo, el máximo de 60 y el 91.15 % de los campos tiene más de una fotografía. En una simulación de partición aleatoria 80/20, el 87.92 % de los registros de validación perteneció a campos que también estaban en el entrenamiento.

![Fotografías por campo, con recorte en el percentil 99.](figuras/02_histograma_fotos_por_campo.png)

La partición oficial de Zindi tampoco separa campos: 2 414 campos y 212 productores aparecen en el entrenamiento y en la prueba. Esta es la razón principal para que el proyecto use su propia partición por campo (sección 5.3).

#### Propiedades técnicas y calidad visual

Todas las fotografías son JPEG. La mediana es de 0.31 megapíxeles y solo el 1.39 % son verticales. LR2020 y SR2020 son por completo de 640 × 480 píxeles. SR2021, en cambio, combina 7 063 imágenes de 320 × 240 con fotografías de varios megapíxeles: el 37.63 % supera los 5 megapíxeles. La prueba de Kolmogórov-Smirnov entre las tres primeras temporadas y SR2021 da su mayor estadístico en los megapíxeles (0.55). La saturación, la exposición, el contraste, el exceso de verde y la nitidez también difieren.

![Megapíxeles por temporada.](figuras/03_caja_megapixeles_temporada.png)

Con el umbral de nitidez establecido, el 1.82 % de las fotografías se clasifica como desenfocada, proporción que sube a 3.67 % en SR2021. El 3.58 % está mal expuesta. Estas fotografías no se eliminaron: representan las condiciones reales de captura que la aplicación recibirá.

![Las diez fotografías con menor nitidez medida.](figuras/03_mosaico_desenfocadas.png)

La huella perceptual agrupó solo 118 imágenes en 51 grupos de fotografías parecidas, y solo 55 imágenes quedaron en grupos mixtos entre entrenamiento y prueba. La inspección de los mosaicos mostró escenas distintas dentro de algunos grupos, así que la duplicación visual es marginal frente al solapamiento por campo.

#### Relación entre el color y la magnitud

El exceso de verde tiene la asociación monótona más fuerte con la magnitud, con una correlación de Spearman de −0.25. Su promedio baja de 0.15 en magnitud 0 a −0.01 en magnitud 100. La relación es consistente con la pérdida de follaje verde, pero moderada: en cada nivel de magnitud hay fotografías con exceso de verde muy distinto.

![Exceso de verde por nivel de magnitud.](figuras/03_caja_verde_magnitud.png)

El mosaico por magnitud ilustra el motivo. Fotografías con la misma magnitud muestran encuadres, iluminación, proporción de cielo y suelo y etapas distintas. Un único atributo de color no basta para estimar la severidad, lo que justifica probar modelos que aprendan texturas y estructura de la escena.

![Ejemplos de sequía ordenados por magnitud.](figuras/03_mosaico_por_magnitud.png)

### 5.5 Implicaciones para el modelado

El análisis exploratorio fijó cinco decisiones de modelado:

1. **Severidad condicionada a sequía.** Los modelos se entrenan solo con registros DR y la regla asigna magnitud cero al resto.
2. **Partición por campo.** Ningún campo aparece en el entrenamiento y en la prueba, ni a ambos lados de la validación.
3. **Métricas en dos alcances.** Se reporta el error dentro de DR, que mide la tarea aprendida, y el global, inflado por los ceros de la regla.
4. **Línea base de color.** Las redes se comparan con un predictor constante y con modelos sobre el exceso de verde y los demás atributos.
5. **Aumentos sin cambio de color.** Las redes reciben recortes y reflejos, pero no alteraciones de tono, porque el color es parte de la señal del daño.
