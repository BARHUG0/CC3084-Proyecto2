import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

from src.config import DIR_FIGURAS, DIR_IMAGENES, PALETA, SECUENCIA_COLORES


def aplicar_estilo():
    plt.rcParams.update(
        {
            "figure.dpi": 100,
            "savefig.dpi": 150,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.grid": True,
            "axes.axisbelow": True,
            "grid.color": "#DDDDDD",
            "axes.prop_cycle": plt.cycler(color=list(SECUENCIA_COLORES)),
            "legend.frameon": False,
            "font.size": 10,
            "axes.titlesize": 12,
            "axes.labelsize": 10,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
        }
    )


def guardar_figura(fig, nombre_archivo):
    DIR_FIGURAS.mkdir(parents=True, exist_ok=True)
    ruta = DIR_FIGURAS / f"{nombre_archivo}.png"
    fig.savefig(ruta, bbox_inches="tight")
    return ruta


def histograma(serie, titulo, etiqueta_x, bins=30, nombre_archivo=None):
    datos = serie.dropna()
    fig, ax = plt.subplots()
    ax.hist(datos, bins=bins, color=PALETA["principal"])
    ax.axvline(datos.mean(), linestyle="--", color=PALETA["terciario"], label="media")
    ax.axvline(datos.median(), linestyle=":", color=PALETA["secundario"], label="mediana")
    ax.set_title(titulo)
    ax.set_xlabel(etiqueta_x)
    ax.set_ylabel("frecuencia")
    ax.legend()
    if nombre_archivo:
        guardar_figura(fig, nombre_archivo)
    return fig


def ecdf(serie, titulo, etiqueta_x, nombre_archivo=None):
    datos = serie.dropna().sort_values()
    y = np.arange(1, len(datos) + 1) / len(datos)
    fig, ax = plt.subplots()
    ax.step(datos, y, where="post", color=PALETA["principal"])
    ax.set_title(titulo)
    ax.set_xlabel(etiqueta_x)
    ax.set_ylabel("proporcion acumulada")
    if nombre_archivo:
        guardar_figura(fig, nombre_archivo)
    return fig


def caja_por_categoria(df, categoria, numerica, titulo, orden=None, nombre_archivo=None):
    if orden is None:
        if hasattr(df[categoria].dtype, "categories"):
            orden = list(df[categoria].dtype.categories)
        else:
            orden = sorted(df[categoria].dropna().unique())
    grupos = [df.loc[df[categoria] == nivel, numerica].dropna() for nivel in orden]
    fig, ax = plt.subplots()
    cajas = ax.boxplot(grupos, tick_labels=[str(n) for n in orden], patch_artist=True)
    for caja, color in zip(cajas["boxes"], SECUENCIA_COLORES * len(orden)):
        caja.set_facecolor(color)
    ax.set_title(titulo)
    ax.set_xlabel(categoria)
    ax.set_ylabel(numerica)
    if nombre_archivo:
        guardar_figura(fig, nombre_archivo)
    return fig


def barras_frecuencia(tabla, titulo, columna_valor="frecuencia", nombre_archivo=None):
    columna_categoria = tabla.columns[0]
    fig, ax = plt.subplots()
    barras = ax.bar(
        tabla[columna_categoria].astype(str), tabla[columna_valor], color=PALETA["principal"]
    )
    ax.bar_label(barras)
    ax.set_title(titulo)
    ax.set_xlabel(columna_categoria)
    ax.set_ylabel(columna_valor)
    if nombre_archivo:
        guardar_figura(fig, nombre_archivo)
    return fig


def barras_apiladas(tabla, titulo, etiqueta_y, nombre_archivo=None):
    fig, ax = plt.subplots()
    posiciones = np.arange(len(tabla))
    base = np.zeros(len(tabla))
    for columna, color in zip(tabla.columns, SECUENCIA_COLORES):
        ax.bar(posiciones, tabla[columna], bottom=base, label=str(columna), color=color)
        base += tabla[columna].to_numpy()
    ax.set_xticks(posiciones)
    ax.set_xticklabels([str(i) for i in tabla.index])
    ax.set_title(titulo)
    ax.set_ylabel(etiqueta_y)
    ax.legend()
    if nombre_archivo:
        guardar_figura(fig, nombre_archivo)
    return fig


def dispersion(df, x, y, titulo, alpha, categoria=None, nombre_archivo=None):
    fig, ax = plt.subplots()
    if categoria is None:
        ax.scatter(df[x], df[y], alpha=alpha, color=PALETA["principal"])
    else:
        for nivel, color in zip(df[categoria].dropna().unique(), SECUENCIA_COLORES):
            subconjunto = df[df[categoria] == nivel]
            ax.scatter(subconjunto[x], subconjunto[y], alpha=alpha, color=color, label=str(nivel))
        ax.legend()
    ax.set_title(titulo)
    ax.set_xlabel(x)
    ax.set_ylabel(y)
    if nombre_archivo:
        guardar_figura(fig, nombre_archivo)
    return fig


def mapa_calor(matriz, titulo, formato_texto=None, mapa_color=None, nombre_archivo=None):
    formato_texto = formato_texto or ".2f"
    valores = matriz.to_numpy(dtype=float)
    fig, ax = plt.subplots()
    imagen = ax.imshow(valores, cmap=mapa_color or "RdBu_r")
    punto_medio = (np.nanmax(valores) + np.nanmin(valores)) / 2
    for i in range(valores.shape[0]):
        for j in range(valores.shape[1]):
            color_texto = "white" if valores[i, j] > punto_medio else "black"
            ax.text(
                j, i, format(valores[i, j], formato_texto), ha="center", va="center",
                color=color_texto,
            )
    ax.set_xticks(range(len(matriz.columns)))
    ax.set_xticklabels(matriz.columns, rotation=45, ha="right")
    ax.set_yticks(range(len(matriz.index)))
    ax.set_yticklabels(matriz.index)
    ax.set_title(titulo)
    fig.colorbar(imagen, ax=ax)
    if nombre_archivo:
        guardar_figura(fig, nombre_archivo)
    return fig


def barras_comparativas(tabla, columnas, titulo, etiqueta_y, nombre_archivo=None):
    fig, ax = plt.subplots()
    posiciones = np.arange(len(tabla))
    ancho = 0.8 / len(columnas)
    for indice, columna in enumerate(columnas):
        ax.bar(
            posiciones + indice * ancho, tabla[columna], width=ancho, label=str(columna),
            color=SECUENCIA_COLORES[indice % len(SECUENCIA_COLORES)],
        )
    ax.set_xticks(posiciones + ancho * (len(columnas) - 1) / 2)
    ax.set_xticklabels([str(i) for i in tabla.index])
    ax.set_title(titulo)
    ax.set_ylabel(etiqueta_y)
    ax.legend()
    if nombre_archivo:
        guardar_figura(fig, nombre_archivo)
    return fig


def mosaico_imagenes(rutas_relativas, subtitulos, titulo, columnas, nombre_archivo=None):
    filas = -(-len(rutas_relativas) // columnas)
    fig, ejes = plt.subplots(filas, columnas, figsize=(columnas * 2.5, filas * 2.5))
    ejes = np.atleast_2d(ejes)
    for indice in range(filas * columnas):
        ax = ejes[indice // columnas, indice % columnas]
        ax.axis("off")
        if indice >= len(rutas_relativas):
            continue
        with Image.open(DIR_IMAGENES / rutas_relativas[indice]) as imagen:
            miniatura = imagen.convert("RGB")
            miniatura.thumbnail((200, 200))
            ax.imshow(miniatura)
        ax.set_title(subtitulos[indice], fontsize=8)
    fig.suptitle(titulo)
    if nombre_archivo:
        guardar_figura(fig, nombre_archivo)
    return fig
