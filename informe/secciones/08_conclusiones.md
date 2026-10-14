## 8. Conclusiones

<!-- Revisar al integrar 02_objetivos.md: cada inciso debe responder a un objetivo específico con su redacción final. -->

**Obtención y preparación de los datos.** El objetivo se cumplió con un flujo reproducible. La descarga, la verificación y la extracción de atributos se ejecutan con una orden cada una y pueden reanudarse si se interrumpen. Las 26 068 fotografías de entrenamiento coinciden uno a uno con los registros de `Train.csv`. Después de la limpieza quedan 23 350 registros aptos para modelado, de los cuales 4 489 tienen diagnóstico de sequía. La partición agrupa por campo y usa una semilla fija. Así ningún campo aparece a ambos lados de la evaluación, y todo el equipo trabaja con la misma partición.

**Análisis de los datos.** El análisis exploratorio mostró tres características que condicionan el modelado:

- Solo el 19 % de las fotografías aptas tiene diagnóstico de sequía.
- La magnitud se concentra en los niveles bajos e intermedios: apenas 44 fotografías DR tienen magnitud 100.
- Las condiciones de captura varían entre temporadas.

Por eso los modelos se entrenaron solo con fotografías DR y se evaluaron por temporada, y el informe distingue entre el alcance DR y el global.

**Construcción y comparación de modelos.** Se entrenó y evaluó una red convolucional preentrenada, ResNet50, frente a un predictor constante que sirve de referencia. La ResNet50 es efectiva para la tarea, aunque con límites:

- Reduce el RMSE sobre las fotografías con sequía de 24.09 a 18.81 puntos (21.9 %) y explica el 39 % de la varianza de la magnitud.
- Mejora a la referencia en las cuatro temporadas.
- Su error de prueba es cercano al de validación, señal de que la evaluación por campo es confiable.
- Comprime las predicciones hacia el centro de la escala. Ordena bien las fotografías por severidad, pero sobrestima los daños leves y subestima los severos. Con un error típico de 15 a 19 puntos, su estimación es útil para priorizar reclamos y apoyar al evaluador, no para reemplazarlo en el cálculo final del monto.

**Ajuste de hiperparámetros.** Las cuatro configuraciones probadas quedaron a menos de un punto de RMSE entre sí, por lo que el desempeño depende más de la información que contienen las fotografías que de estos hiperparámetros. El sobreajuste aparece pronto: con el último bloque descongelado, la mejor época fue la segunda. Las mejoras más prometedoras están en los datos y no en la arquitectura:

- Más fotografías de daños severos.
- Ponderar los niveles poco frecuentes.
- Tratar la magnitud como una variable ordinal de diez niveles.

**Costo computacional.** El entrenamiento completo de la ResNet50 tardó 11.4 minutos en la GPU de una laptop con Apple Silicon, y la inferencia 13 ms por fotografía. Una red de este tamaño puede entrenarse y servirse en hardware de consumo, sin GPU dedicada, y responder en línea desde la aplicación.

**Aplicación.** La API y la interfaz web permiten consultar los datos, comparar los modelos y estimar la magnitud de una fotografía nueva. Cada modelo entrenado aparece en la aplicación sin cambios en el contrato, porque cumple la interfaz común de `ModeloMagnitud`.

**Trabajo pendiente.** Faltan los resultados de la regresión sobre exceso de verde, de Random Forest y de DenseNet121. Al ejecutar de nuevo el cuaderno de comparación se sumarán a las figuras y a la recomendación con el mismo criterio, el menor RMSE sobre las fotografías con sequía.
