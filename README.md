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
