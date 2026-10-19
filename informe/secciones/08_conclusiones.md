## 8. Conclusiones

**Obtención y preparación de los datos.** El objetivo se cumplió con un flujo reproducible. La descarga, la verificación y la extracción de atributos se ejecutan con una orden cada una y pueden reanudarse si se interrumpen. Las 26 068 fotografías de entrenamiento coinciden uno a uno con los registros de `Train.csv`. Después de la limpieza quedan 23 350 registros aptos para modelado, de los cuales 4 489 tienen diagnóstico de sequía. La partición agrupa por campo y usa una semilla fija. Así ningún campo aparece a ambos lados de la evaluación, y todo el equipo trabaja con la misma partición.

**Análisis de los datos.** El análisis exploratorio mostró tres características que condicionan el modelado:

- Solo el 19 % de las fotografías aptas tiene diagnóstico de sequía, y únicamente esas tienen una magnitud distinta de cero.
- Las fotografías se agrupan por campo: en una partición aleatoria, casi nueve de cada diez registros de validación pertenecerían a campos ya vistos.
- Las condiciones de captura varían entre temporadas, sobre todo en SR2021, que mezcla fotografías de baja y de alta resolución.

Por eso los modelos se entrenaron solo con fotografías DR, la partición separa campos y el informe distingue entre el alcance DR y el global.

**Construcción y comparación de modelos.** Se entrenaron y evaluaron seis modelos sobre la misma partición. Los cinco que aprenden de los datos superan al predictor constante, cuyo RMSE DR es de 24.09:

- Los modelos sobre atributos globales mejoran poco. La regresión sobre exceso de verde llega a 21.44 y el Random Forest, a 20.61, con R² de 0.21 y 0.27.
- Las redes convolucionales mejoran más. DenseNet121 llega a 19.36; la ResNet50, a 18.33, y la ResNet50 ajustada, a 17.84. Explican del 35 % al 45 % de la varianza de la magnitud.
- Con el mismo procedimiento, la ResNet50 supera a DenseNet121 por un punto de RMSE, una diferencia significativa según el bootstrap pareado.
- Todos los modelos mejoran a la referencia en las cuatro temporadas, y su error de prueba es cercano al de validación, señal de que la evaluación por campo es confiable.
- Todos comprimen las predicciones hacia el centro de la escala. Las redes ordenan bien las fotografías por severidad, pero sobrestiman los daños leves y subestiman los severos. Con un error típico de 13 a 19 puntos, su estimación es útil para priorizar reclamos y apoyar al evaluador, no para reemplazarlo en el cálculo final del monto.

El contraste entre familias responde al problema científico: aprender la representación de la fotografía reduce el error casi tres puntos de RMSE respecto del mejor modelo sobre atributos. El exceso de verde resume buena parte de la señal de color, y concentra casi la mitad de la importancia del Random Forest, pero la textura y la estructura de la escena aportan información que los promedios no capturan.

**Ajuste de hiperparámetros y de la receta.** Los hiperparámetros se eligieron con validación agrupada por campo, y cada configuración probada quedó registrada con su error de validación. En los tres algoritmos con búsqueda, el error dependió poco de la configuración. Las 30 combinaciones del Random Forest quedaron a 0.4 puntos de RMSE entre sí, y las cuatro configuraciones de la ResNet50, a menos de un punto. En DenseNet121, la diferencia llegó a dos puntos porque ajustar su último bloque con la tasa mayor sobreajustó desde la segunda época.

La receta combinada de la ResNet50 ajustada sí mejoró de forma consistente. Consiste en ajustar toda la red con tasas por capa y programa coseno, y en usar una entrada de 320 y el promedio con el reflejo de la imagen. En los pliegues de validación redujo el RMSE de 19.58 a 17.91. En la prueba redujo el MAE de 14.61 a 13.50, una diferencia significativa, y el RMSE de 18.33 a 17.84.

El cambio individual más útil fue la resolución de entrada. Una explicación probable es que, al reducir menos las fotografías, se conservan detalles de las hojas que la entrada de 224 pierde. Una lección práctica es evaluar en varios pliegues con una política fija: en un solo pliegue y eligiendo la mejor época, las diferencias de menos de un punto se confunden con ruido.

Las mejoras siguientes más prometedoras están en los datos y no en la arquitectura:

- Más fotografías de daños severos.
- Ponderar los niveles poco frecuentes.
- Tratar la magnitud como una variable ordinal de diez niveles.

**Costo computacional.** Los seis modelos se entrenaron en la misma laptop. Los modelos sobre atributos se entrenan en segundos en la CPU y predicen en centésimas de milisegundo. Las redes tardaron de 10 a 17 minutos en una GPU de laptop y predicen en 20 a 31 ms por fotografía. Todas pueden entrenarse y servirse en hardware de consumo y responder en línea desde la aplicación.

La elección del modelo depende de la prioridad. El criterio del proyecto prefiere el más rápido cuando el RMSE difiere en menos de un punto, y recomienda la ResNet50. Si la latencia no es una restricción, la ajustada ofrece el menor error. Si no hay GPU y se necesita una respuesta instantánea, el Random Forest es una alternativa con un error 2.3 puntos mayor que la ResNet50.

**Aplicación.** La API y la interfaz web permiten consultar los datos, comparar los modelos y estimar la magnitud de una fotografía nueva con uno o con todos los modelos. Cada modelo entrenado aparece en la aplicación sin cambios en el contrato, porque cumple la interfaz común de `ModeloMagnitud`.
