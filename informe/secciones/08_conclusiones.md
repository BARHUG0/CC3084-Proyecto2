## 8. Conclusiones

<!-- Revisar al integrar 02_objetivos.md: cada inciso debe responder a un objetivo específico con su redacción final. -->

**Obtención y preparación de los datos.** El objetivo se cumplió con un flujo reproducible. La descarga, la verificación y la extracción de atributos se ejecutan con una orden cada una y pueden reanudarse si se interrumpen. Las 26 068 fotografías de entrenamiento coinciden uno a uno con los registros de `Train.csv`. Después de la limpieza quedan 23 350 registros aptos para modelado, de los cuales 4 489 tienen diagnóstico de sequía. La partición agrupa por campo y usa una semilla fija. Así ningún campo aparece a ambos lados de la evaluación, y todo el equipo trabaja con la misma partición.

**Análisis de los datos.** El análisis exploratorio mostró tres características que condicionan el modelado:

- Solo el 19 % de las fotografías aptas tiene diagnóstico de sequía.
- La magnitud se concentra en los niveles bajos e intermedios: apenas 44 fotografías DR tienen magnitud 100.
- Las condiciones de captura varían entre temporadas.

Por eso los modelos se entrenaron solo con fotografías DR y se evaluaron por temporada, y el informe distingue entre el alcance DR y el global.

**Construcción y comparación de modelos.** Se entrenaron y evaluaron dos versiones de una red convolucional preentrenada, ResNet50, frente a un predictor constante que sirve de referencia. Ambas son efectivas para la tarea, aunque con límites:

- Reducen el RMSE sobre las fotografías con sequía de 24.09 a 18.81 puntos (ResNet50) y a 18.09 (ResNet50 ajustada). Explican el 39 % y el 44 % de la varianza de la magnitud.
- Mejoran a la referencia en las cuatro temporadas.
- Su error de prueba es cercano al de validación, señal de que la evaluación por campo es confiable.
- Comprimen las predicciones hacia el centro de la escala. Ordenan bien las fotografías por severidad, pero sobrestiman los daños leves y subestiman los severos. Con un error típico de 14 a 19 puntos, su estimación es útil para priorizar reclamos y apoyar al evaluador, no para reemplazarlo en el cálculo final del monto.

**Ajuste de hiperparámetros y de la receta.** Las cuatro configuraciones de la búsqueda de la ResNet50 quedaron a menos de un punto de RMSE entre sí. Siete cambios probados uno a la vez tampoco movieron el error más que la variación entre épocas.

La receta combinada sí mejoró de forma consistente. Consiste en ajustar toda la red con tasas por capa y programa coseno, y en usar una entrada de 320 y el promedio con el reflejo de la imagen. En los pliegues de validación redujo el RMSE de 19.58 a 17.91. En la prueba redujo el MAE de 15.03 a 13.84, una diferencia significativa, y el RMSE de 18.81 a 18.09.

El cambio individual más útil fue la resolución de entrada. Una explicación probable es que, al reducir menos las fotografías, se conservan detalles de las hojas que la entrada de 224 pierde. Una lección práctica es evaluar en varios pliegues con una política fija: en un solo pliegue y eligiendo la mejor época, las diferencias de menos de un punto se confunden con ruido.

Las mejoras siguientes más prometedoras están en los datos y no en la arquitectura:

- Más fotografías de daños severos.
- Ponderar los niveles poco frecuentes.
- Tratar la magnitud como una variable ordinal de diez niveles.

**Costo computacional.** El entrenamiento completo de la ResNet50 tardó 11.4 minutos en la GPU de una laptop con Apple Silicon, y su inferencia 13 ms por fotografía. La versión ajustada requiere unos 32 minutos con el equipo conectado y 29 ms por fotografía. Ambas redes pueden entrenarse y servirse en hardware de consumo, sin GPU dedicada, y responder en línea desde la aplicación.

La elección entre ellas depende de la prioridad. El criterio del proyecto prefiere la más rápida cuando el RMSE difiere en menos de un punto, y recomienda la ResNet50. Si la latencia no es una restricción, la ajustada ofrece el menor error.

**Aplicación.** La API y la interfaz web permiten consultar los datos, comparar los modelos y estimar la magnitud de una fotografía nueva. Cada modelo entrenado aparece en la aplicación sin cambios en el contrato, porque cumple la interfaz común de `ModeloMagnitud`.

**Trabajo pendiente.** Faltan los resultados de la regresión sobre exceso de verde, de Random Forest y de DenseNet121. Al ejecutar de nuevo el cuaderno de comparación se sumarán a las figuras y a la recomendación con el mismo criterio, el menor RMSE sobre las fotografías con sequía.
