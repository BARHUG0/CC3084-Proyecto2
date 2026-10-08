# Contrato de la API

Este directorio es la fuente de verdad entre el backend y el frontend.

- `openapi.json`: contrato completo generado por FastAPI a partir de `src/esquemas.py` y `src/api.py`.
- `ejemplos/*.json`: respuestas reales de la API sobre un conjunto sintetico. Sirven como datos simulados para desarrollar el frontend sin backend.
- `ejemplos/indice.json`: metodo, ruta, parametros y codigo HTTP que produjo cada ejemplo.

## Levantar la API

```powershell
uvicorn src.api:app --reload --port 8000
```

- URL base: `http://localhost:8000/api`
- Documentacion interactiva: `http://localhost:8000/docs`
- CORS habilitado para `http://localhost:5173` y `http://127.0.0.1:5173`, el puerto por defecto de Vite.

La API arranca aunque no existan datos ni modelos. En ese caso `/api/salud` lo informa, las rutas de datos responden `503` y las metricas devuelven listas vacias.

Para habilitar todo con datos reales:

1. Descargar datos y extraer atributos con el flujo existente del proyecto.
2. Ejecutar `python -m src.conjunto` para crear `data/procesado/conjunto_modelado.parquet`.
3. Colocar los artefactos de cada modelo en `data/procesado/modelos/` y sus resultados en `data/procesado/resultados/`.

La API detecta archivos nuevos o actualizados sin reiniciarse.

## Generar tipos para React

```powershell
npx openapi-typescript contrato/openapi.json -o app/src/api/esquema.ts
```

## Convenciones

- Todas las rutas usan el prefijo `/api` y responden JSON, excepto la imagen de un registro, que responde `image/jpeg`.
- Los nombres de campos estan en espanol y en `snake_case`.
- Los codigos de temporada, dano y etapa son los del conjunto original. `/api/catalogos` entrega sus nombres legibles y la paleta de colores del proyecto.
- La magnitud siempre esta entre 0 y 100. `magnitud_redondeada` es un multiplo de 10.
- Los parametros que aceptan varios valores se repiten: `?modelos=constante&modelos=random_forest`. En `multipart/form-data`, el campo `modelos` tambien se repite.
- Las metricas se calculan sobre el subconjunto `prueba`, separado por campo. `alcance=dr` usa solo registros de sequia; `alcance=global` usa todos y asigna 0 a los diagnosticos distintos de DR.
- Ningun campo se elimina ni cambia de tipo sin regenerar este contrato y actualizar las pruebas.

## Rutas

| Metodo | Ruta | Parametros | Respuesta |
|:--|:--|:--|:--|
| GET | `/api/salud` | | `Salud` |
| GET | `/api/catalogos` | | `Catalogos` |
| GET | `/api/datos/variables` | | `Variable[]` |
| GET | `/api/datos/resumen` | | `ResumenDatos` |
| GET | `/api/datos/registros` | `pagina`, `tamano` hasta 100, `temporada`, `dano`, `etapa`, `subconjunto`, `magnitud_min`, `magnitud_max`, `orden`, `descendente` | `PaginaRegistros` |
| GET | `/api/datos/registros/{registro_id}/imagen` | `lado` de 64 a 1024 | `image/jpeg` |
| GET | `/api/datos/distribucion/{variable}` | `por`: `ninguno`, `dano`, `temporada` o `etapa`; `bins` de 5 a 50; `solo_dr` | `Distribucion` |
| GET | `/api/datos/dispersion` | `x`, `y`, `solo_dr`, `muestra` hasta 5000 | `Dispersion` |
| GET | `/api/datos/correlaciones` | `solo_dr` | `Correlacion[]` |
| GET | `/api/modelos` | | `ModeloInfo[]` |
| GET | `/api/modelos/{modelo_id}` | | `ModeloDetalle` |
| GET | `/api/metricas` | `modelos` repetible, `alcance` | `Metricas[]` |
| GET | `/api/metricas/{modelo_id}/predicciones` | `alcance`, `limite` | `PuntoPrediccion[]` |
| GET | `/api/metricas/{modelo_id}/errores` | `por`: `temporada`, `etapa` o `magnitud`; `alcance` | `ErrorGrupo[]` |
| POST | `/api/predecir` | multipart: `imagen` obligatoria, `dano` opcional, `modelos` repetible | `Prediccion` |

Detalles relevantes para la interfaz:

- `PaginaRegistros.paginas` puede ser 0. Una pagina fuera de rango devuelve `registros: []`, no un error.
- En `Distribucion`, todos los grupos comparten `bordes`; cada grupo tiene `len(bordes) - 1` conteos. Para `magnitud`, los bordes van de -5 a 105 en pasos de 10, de modo que cada barra queda centrada en una decena.
- `ModeloInfo.disponible` indica si el modelo puede usarse en `/api/predecir`. `ModeloInfo.tiene_resultados` indica si aparece en `/api/metricas`.
- `ModeloInfo.entradas` lista variables de `/api/datos/variables` o el valor `imagen_rgb` para las redes convolucionales.
- `/api/metricas` omite los modelos sin resultados. Las rutas de un modelo concreto responden `409 sin_resultados`.
- `ModeloDetalle` incluye `historial_ajuste`, `curva_entrenamiento` e `importancias`. Pueden venir vacios segun la familia del modelo.
- En `/api/predecir`, si `dano` se omite o llega vacio, se asume sequia y se agrega una advertencia. Si `dano` es distinto de `DR`, cada modelo devuelve 0 con `regla_aplicada: true`. Si solo algunos modelos fallan, la respuesta es 200 con sus predicciones y una advertencia por cada modelo omitido; `error_modelo` se reserva para cuando fallan todos.

## Errores

Todo error responde con `{"detalle": string, "codigo": string}`. Los errores fuera del contrato usan la familia `http_*` (`http_404`, `http_405`), donde el sufijo es el codigo de estado.

| HTTP | `codigo` | Cuando ocurre |
|:--|:--|:--|
| 400 | `imagen_invalida` | El archivo no puede abrirse como imagen. |
| 404 | `modelo_no_encontrado` | El identificador de modelo no existe. |
| 404 | `registro_no_encontrado` | El identificador de registro no existe. |
| 404 | `imagen_no_disponible` | La fotografia no esta descargada en el servidor. |
| 404 | `http_404` | La ruta no existe. |
| 405 | `http_405` | El metodo HTTP no esta permitido en la ruta. |
| 409 | `sin_resultados` | El modelo aun no tiene resultados de prueba. |
| 409 | `modelo_no_disponible` | Se pidio un modelo sin artefacto entrenado. |
| 409 | `sin_modelos_disponibles` | Ningun modelo tiene artefacto entrenado. |
| 413 | `imagen_demasiado_grande` | La imagen supera 15 MB o 50 megapixeles. |
| 415 | `formato_no_soportado` | La imagen no es JPEG ni PNG. |
| 422 | `validacion` | Un parametro no cumple el contrato; incluye `magnitud_min` mayor que `magnitud_max`. |
| 500 | `error_modelo` | Todos los modelos seleccionados fallaron al predecir. |
| 503 | `datos_no_disponibles` | No existe el conjunto de modelado. |

## Mantener el contrato

```powershell
python -m src.contrato
pytest
```

El primer comando regenera `openapi.json` y los ejemplos. La prueba `test_openapi_exportado_coincide_con_la_api` falla si el codigo cambia y el contrato no se regenera.
