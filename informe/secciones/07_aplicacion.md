## 7. Aplicación

La aplicación web presenta los datos, los modelos y sus resultados de forma interactiva. Está construida con React y TypeScript sobre Vite, con componentes de estilo neobrutalista, gráficos de Recharts y una paleta agrícola de verde, oro y terracota. Se comunica con la API de FastAPI mediante un cliente tipado que se genera desde el contrato OpenAPI del proyecto, de modo que cualquier cambio en el contrato se refleja de inmediato en los tipos del código.

La escala de magnitud del daño usa un degradado continuo de verde a terracota. El color nunca aparece solo: siempre acompaña al número o a una etiqueta, y la paleta se verificó para contraste WCAG AA y para distinguirse con los tipos más comunes de daltonismo. Cuando la API no responde o faltan datos o modelos, cada página muestra un aviso con la instrucción para resolverlo en lugar de quedar vacía.

La aplicación tiene cinco páginas y muestra los datos y los resultados reales del proyecto. La página de inicio resume el estado de la API, el tamaño del conjunto (23 350 fotografías de 3 051 campos, 4 489 con sequía) y la partición entre entrenamiento y prueba.

![Página de inicio con el estado del sistema y el resumen del conjunto.](figuras/app_inicio.png)

La página de exploración muestra la composición del conjunto, un histograma configurable por variable, agrupación e intervalos, la dispersión de cada atributo contra la magnitud y la correlación de Spearman. Al final incluye una tabla de registros con filtros, orden por columna y paginación.

![Página de exploración de datos.](figuras/app_explorar.png)

Al abrir un registro se muestra su fotografía junto con sus atributos y su diagnóstico. La figura muestra una fotografía de prueba con sequía de magnitud 100: el suelo queda expuesto y el exceso de verde es negativo.

![Detalle de un registro con su fotografía.](figuras/app_explorar_registro.png)

La página de modelos describe cada algoritmo: su familia, las variables que usa, los hiperparámetros elegidos, el historial de la búsqueda de hiperparámetros, la curva de entrenamiento y la importancia de las variables cuando el modelo las reporta. La figura muestra las cuatro configuraciones evaluadas para DenseNet121, con la elegida resaltada en terracota.

![Página de modelos.](figuras/app_modelos.png)

La página de rendimiento compara los seis modelos sobre el conjunto de prueba. Muestra MAE, RMSE, R² y tiempos de entrenamiento e inferencia, el gráfico de valor real contra predicho, la distribución del error y el error por temporada, etapa o magnitud. La evaluación puede limitarse a los registros con sequía o abarcar todo el conjunto de prueba, y cada modelo puede mostrarse u ocultarse desde la leyenda.

![Página de rendimiento de los modelos.](figuras/app_rendimiento.png)

La página de predicción recibe una fotografía JPEG o PNG, un diagnóstico opcional y los modelos a consultar. Devuelve la magnitud estimada por cada modelo, redondeada a la decena más cercana, e indica cuándo se aplica la regla que fija la magnitud en 0 para diagnósticos distintos de sequía. Antes de estimar, la API calcula los atributos de la fotografía y aplica a cada red su propia transformación, sin que el usuario intervenga. La figura usa una fotografía de prueba con magnitud real de 60, elegida para ilustrar el resultado: las tres redes y el Random Forest estiman entre 50 y 60, mientras que el predictor constante devuelve siempre 40.

![Página de predicción con el resultado de una fotografía.](figuras/app_predecir.png)

Las capturas se tomaron con los datos y los modelos reales del proyecto. El repositorio incluye el conjunto de modelado, los resultados de prueba de los seis modelos y los modelos tabulares, de modo que la exploración, la comparación y la predicción con los modelos tabulares funcionan al clonarlo. Los pesos de las redes y las fotografías ocupan demasiado para el repositorio y se obtienen de la carpeta compartida del equipo. Sin ellos, la aplicación marca las redes como «Sin artefacto» y avisa que la fotografía del registro no está disponible.
