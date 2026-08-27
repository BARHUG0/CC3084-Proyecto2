# CGIAR Eyes on the Ground

Analisis exploratorio y preprocesamiento de datos para el desafio "CGIAR Eyes on the Ground":
prediccion de la magnitud del dano por sequia en cultivos a partir de fotografias tomadas por
pequenos productores de Africa oriental.

## Estructura del repositorio

| Carpeta | Contenido |
|---|---|
| `src` | Modulos de descarga, carga, limpieza, extraccion de caracteristicas, tablas y graficos |
| `notebooks` | Cuadernos de adquisicion y analisis exploratorio |
| `informe` | Informe final y sus figuras |
| `data` | Datos descargados y derivados (excluido del control de versiones) |

## Requisitos

Python 3.11 o superior. Funciona en Windows, Linux y macOS.

```bash
python -m venv .venv
python -m pip install -r requirements.txt
```

En Linux, `keyring` requiere un servicio de almacenamiento de secretos: `gnome-keyring` junto con
`dbus` en distribuciones GNOME, `kwalletmanager` en entornos KDE. Windows y macOS no requieren
configuracion adicional.

## Credenciales

El token de Zindi se obtiene desde el enlace de descarga en la pestana de datos de la
competencia, en el parametro `auth_token`.

```bash
python -m src.credenciales guardar
python -m src.credenciales borrar
python -m src.credenciales estado
```

## Obtencion de datos

```bash
python -m src.descarga csv
python -m src.descarga imagenes
python -m src.descarga todo
python -m src.descarga verificar
```

Las imagenes ocupan 8.7 GB comprimidas y alrededor de 18 GB descomprimidas. El proceso es
reanudable: si se interrumpe, ejecutar la misma orden retoma la descarga sin repetir los archivos
ya completos. Si Google Drive rechaza la descarga masiva por limite de cuota, descargue
manualmente `train.zip` y `test.zip` desde la carpeta compartida y coloquelos en `data/crudo`
antes de reintentar.

## Extraccion de caracteristicas de imagen

```bash
python -m src.caracteristicas --particion todas
```

Construye una cache en `data/procesado/caracteristicas_imagenes.parquet` con atributos numericos
de cada imagen (brillo, nitidez, saturacion, huella perceptual, entre otros). El proceso es
reanudable: si se interrumpe, la misma orden continua sin reprocesar lo ya cacheado. Use
`--limite` para probar sobre una muestra pequena y `--desde-cero` para ignorar la cache existente.

## Orden de ejecucion de los cuadernos

1. `01_adquisicion_datos.ipynb`
2. `02_eda_tabular.ipynb`
3. `03_eda_imagenes.ipynb`

## Fuentes

[CGIAR Eyes on the Ground Challenge en Zindi](https://zindi.africa/competitions/cgiar-eyes-on-the-ground-challenge)
