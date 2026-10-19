## 1. Introducción

### Situación problemática

ACRE Africa ofrece seguros agrícolas a pequeños productores de África oriental. Cuando un productor presenta un reclamo, la empresa lo resuelve con fotografías que el propio productor toma con su teléfono: un evaluador revisa cada imagen, identifica el tipo de daño y estima el porcentaje de pérdida. Esa revisión manual requiere tiempo y retrasa la liquidación de los reclamos. Como una proporción considerable de los reclamos se relaciona con sequía, el reto CGIAR Eyes on the Ground plantea automatizar la estimación de su magnitud a partir de las fotografías (Zindi, 2023).

El conjunto de datos proviene del proyecto Eyes on the Ground, que reunió fotografías de campos de pequeños productores en Kenia junto con etiquetas de etapa de crecimiento, tipo de daño y magnitud (Waithaka et al., 2022). ACRE Africa e IFPRI desarrollaron el proyecto con apoyo de Lacuna Fund (CGIAR, 2021).

El análisis exploratorio de la etapa anterior delimitó tres condiciones del problema:

- Solo el 17 % de las fotografías de entrenamiento tiene diagnóstico de sequía, y únicamente esas tienen una magnitud distinta de cero.
- Las fotografías se agrupan por campo. En una partición aleatoria, el 87.92 % de los registros de validación pertenecía a campos que también aparecían en el entrenamiento, lo que infla la evaluación.
- Las condiciones de captura cambian entre temporadas. En SR2021 la resolución media sube de 0.49 a 3.39 megapíxeles, y la nitidez y la saturación también se desplazan.

### Problema científico

¿Con qué error se puede estimar la magnitud del daño por sequía a partir de una fotografía, cuando la evaluación separa los campos de entrenamiento y de prueba? ¿Qué tipo de modelo lo consigue con un costo compatible con una aplicación en línea: los que usan atributos visuales globales o las redes convolucionales preentrenadas?

### Contenido del informe

- La sección 2 plantea los objetivos.
- La sección 3 resume el marco teórico sobre procesamiento de imágenes, análisis agrícola de fotografías y algoritmos útiles para el problema.
- La sección 4 describe la metodología: los pasos seguidos, la selección de los conjuntos, los algoritmos y las herramientas.
- La sección 5 presenta los datos, su limpieza y el análisis exploratorio.
- La sección 6 reporta el ajuste y la comparación de los modelos.
- La sección 7 describe la aplicación web.
- La sección 8 cierra con las conclusiones sobre cada objetivo.
