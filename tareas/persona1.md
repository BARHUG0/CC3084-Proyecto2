# Persona 1: modelos tabulares e introducción del informe

## Objetivo

Construir y ajustar los modelos que usan atributos visuales globales: una regresión lineal sobre exceso de verde y Random Forest Regressor. También redactar la introducción, los objetivos y la metodología del informe.

Esta tarea no depende de las otras dos. Puede hacerse en cualquier orden.

## Preparación común

1. Activar el entorno del directorio superior e instalar dependencias:
   ```powershell
   uv pip install -r requirements.txt
   ```
2. Obtener los datos con el flujo existente del proyecto: descarga, `python -m src.caracteristicas` y el cuaderno `01_adquisicion_datos.ipynb`.
3. Crear el conjunto de modelado:
   ```powershell
   python -m src.conjunto
   ```
   La partición entre entrenamiento y prueba se agrupa por campo y usa una semilla fija. Todo el equipo obtiene la misma partición. No se debe modificar `src/particiones.py` ni `SEMILLA` en `src/config.py`.
4. Confirmar que las pruebas pasan antes de empezar:
   ```powershell
   pytest
   ```

## Reglas compartidas

- Se entrena únicamente con `subconjunto == "entrenamiento"`. El subconjunto `prueba` solo se usa una vez, al final, para guardar resultados.
- El ajuste de hiperparámetros usa `pliegues_por_campo` de `src/particiones.py`, para que un mismo campo nunca quede a ambos lados de la validación.
- Los modelos estiman severidad condicionada a sequía. Se entrenan con `entrenamiento_y_prueba(conjunto, solo_dr=True)` y se evalúan con `completar_con_regla`, que asigna 0 a los diagnósticos distintos de DR.
- No se modifican `src/esquemas.py`, `src/api.py` ni `contrato/`. El contrato con el frontend ya está fijado.
- Cada modelo hereda de `ModeloMagnitud` en `src/modelo_base.py` y se agrega a `CLASES_MODELOS` en `src/registro_modelos.py`.
- `ejecutar_referencia_constante` en `src/modelos_tabulares.py` es el ejemplo completo a imitar.

## Entregables

### 1. Regresión lineal sobre exceso de verde

En `src/modelos_tabulares.py`:

- Clase `RegresionExcesoVerde` con `id = "regresion_exceso_verde"`, `familia = "referencia"`, `entradas = ("exceso_verde",)` y `extension = ".joblib"`.
- `predecir(imagen, atributos)` usa `atributos["exceso_verde"]`.
- Función `ejecutar_regresion_exceso_verde(conjunto, dir_modelos, dir_resultados)` que entrena, guarda el artefacto y llama a `guardar_resultados`.

### 2. Random Forest Regressor

En `src/modelos_tabulares.py`:

- Clase `RandomForestMagnitud` con `id = "random_forest"` y `familia = "tabular"`.
- Entradas iniciales: `exceso_verde`, `saturacion`, `brillo`, `contraste`, `media_r`, `media_g`, `media_b`, `prop_sobreexpuesta` y `prop_subexpuesta`. La revisión bibliográfica advierte que `megapixeles` y `nitidez` pueden describir el dispositivo o la temporada más que el daño. Si se prueban, debe compararse el resultado con y sin ellas y justificarse la decisión.
- Ajuste con `RandomizedSearchCV` sobre `n_estimators`, `max_depth`, `min_samples_leaf` y `max_features`. Se usa `cv=pliegues_por_campo(entrenamiento)`, la métrica `neg_root_mean_squared_error` y alrededor de 30 combinaciones.
- `guardar_resultados` recibe:
  - `hiperparametros`: los mejores encontrados.
  - `historial_ajuste`: una entrada por combinación, con `parametros`, `rmse_validacion` y `mae_validacion`.
  - `importancias`: una entrada por variable, con `variable` e `importancia`.
- Función `ejecutar_random_forest(conjunto, dir_modelos, dir_resultados, n_iter=30)`.

### 3. Registro

Agregar `RegresionExcesoVerde` y `RandomForestMagnitud` a `CLASES_MODELOS`.

### 4. Cuaderno `notebooks/04_modelos_tabulares.ipynb`

- Ejecuta los modelos de referencia constante y de exceso de verde, y Random Forest, usando funciones de `src/`.
- Muestra la tabla del ajuste de hiperparámetros.
- Guarda la figura `informe/figuras/04_importancia_atributos.png` con la `PALETA` de `src/config.py`.
- Compara la generalización temporal: entrena con `separar_por_temporada` y reporta cuántos campos comparten ambas partes con `campos_compartidos`.

### 5. Informe

Redactar en `informe/secciones/`:

- `01_introduccion.md`: contenido del informe y planteamiento del problema.
- `02_objetivos.md`: objetivo general y objetivos específicos. Las conclusiones del informe deben responder a cada uno.
- `04_metodologia.md`: pasos seguidos, selección de los conjuntos de entrenamiento y prueba, selección de algoritmos, herramientas, recursos de cómputo, lenguajes y bibliotecas. Incluye la justificación de FastAPI y React.

El informe completo se genera con:
```powershell
quarto render informe/informe_final.md --to pdf
```

## Criterios de terminado

- `pytest` pasa.
- `uvicorn src.api:app` muestra `regresion_exceso_verde` y `random_forest` con `disponible: true` y `tiene_resultados: true` en `/api/modelos`.
- `/api/modelos/random_forest` devuelve `historial_ajuste` e `importancias` no vacíos.
- Los archivos `data/procesado/modelos/<id>.joblib` y `data/procesado/resultados/<id>.json` se comparten en la carpeta común del equipo, porque `data/` no se versiona.

## Commits sugeridos

- `feat: agrega regresion lineal sobre exceso de verde`
- `feat: agrega random forest con ajuste por campo`
- `feat: registra los modelos tabulares`
- `feat: agrega cuaderno de modelos tabulares`
- `docs: redacta introduccion objetivos y metodologia`
