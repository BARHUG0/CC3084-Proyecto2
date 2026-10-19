import { useState } from "react"

import type { AgrupacionError, Alcance, Metricas, ModeloInfo, PuntoPrediccion } from "@/api/cliente"
import { useErrores, useMetricas, useModelos, usePredicciones } from "@/api/consultas"
import { Bloque } from "@/components/Bloque"
import { Alternador, Selector } from "@/components/Controles"
import { Encabezado } from "@/components/Encabezado"
import { AvisoError, Cargando, Contenido, Vacio } from "@/components/Estados"
import { GraficoBarras, type FilaGrafico } from "@/components/graficos/GraficoBarras"
import { GraficoDispersion } from "@/components/graficos/GraficoDispersion"
import { Metrica } from "@/components/Metrica"
import { SelectorModelos } from "@/components/SelectorModelos"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { colorSerie } from "@/lib/colores"
import { duracion, entero, numero } from "@/lib/formato"
import { filtrarSeleccion, useModeloSeleccionado } from "@/lib/seleccion"
import { cn } from "@/lib/utils"

type ModeloColor = ModeloInfo & { color: string }

const ALCANCES: { valor: Alcance; etiqueta: string }[] = [
  { valor: "dr", etiqueta: "Solo sequía" },
  { valor: "global", etiqueta: "Todos los registros" },
]

const AGRUPACIONES: { valor: AgrupacionError; etiqueta: string }[] = [
  { valor: "temporada", etiqueta: "Temporada" },
  { valor: "etapa", etiqueta: "Etapa" },
  { valor: "magnitud", etiqueta: "Magnitud real" },
]

type ConsultaModelo<T> = { modelo: ModeloColor; datos: T; error: unknown; isPending: boolean }
type ConsultaFallida = { modelo: ModeloColor; error: unknown }

function porModelo<T>(consultas: { data: T | undefined; error: unknown; isPending: boolean }[], modelos: ModeloColor[]) {
  const lista = modelos.map((modelo, i) => ({
    modelo,
    datos: consultas[i].data,
    error: consultas[i].error,
    isPending: consultas[i].isPending,
  }))
  return {
    isPending: lista.every((c) => c.datos === undefined && c.isPending),
    disponibles: lista.filter((c): c is ConsultaModelo<T> => c.datos !== undefined),
    fallidos: lista.filter((c) => c.datos === undefined && !c.isPending).map(({ modelo, error }) => ({ modelo, error })),
  }
}

function NotaFallidos({ fallidos }: { fallidos: ConsultaFallida[] }) {
  if (fallidos.length === 0) return null
  return (
    <Alert status="warning">
      <AlertTitle className="font-head">Modelos sin respuesta</AlertTitle>
      <AlertDescription>
        No se pudieron cargar los datos de {fallidos.map((f) => f.modelo.nombre).join(", ")}. El gráfico muestra solo los modelos
        disponibles.
      </AlertDescription>
    </Alert>
  )
}

function mejor(metricas: Metricas[], clave: "mae" | "rmse" | "r2" | "tiempo_inferencia_ms") {
  const valores = metricas.map((m) => m[clave]).filter((v): v is number => v !== null)
  if (valores.length < 2) return null
  return clave === "r2" ? Math.max(...valores) : Math.min(...valores)
}

function TablaMetricas({ metricas, modelos }: { metricas: Metricas[]; modelos: ModeloColor[] }) {
  const columnas = [
    { clave: "mae", titulo: "MAE", formato: (m: Metricas) => numero(m.mae, 2) },
    { clave: "rmse", titulo: "RMSE", formato: (m: Metricas) => numero(m.rmse, 2) },
    { clave: "r2", titulo: "R²", formato: (m: Metricas) => numero(m.r2, 3) },
    { clave: "tiempo_inferencia_ms", titulo: "Inferencia", formato: (m: Metricas) => `${numero(m.tiempo_inferencia_ms, 3)} ms` },
  ] as const
  const mejores = Object.fromEntries(columnas.map((columna) => [columna.clave, mejor(metricas, columna.clave)]))
  return (
    <div className="self-start overflow-x-auto border-2">
      <Table>
        <TableHeader>
          <TableRow className="bg-secondary hover:bg-secondary">
            <TableHead className="font-head">Modelo</TableHead>
            <TableHead className="text-right font-head">n</TableHead>
            {columnas.map((columna) => (
              <TableHead key={columna.clave} className="text-right font-head">
                {columna.titulo}
              </TableHead>
            ))}
            <TableHead className="text-right font-head">Entrenamiento</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {metricas.map((metrica) => {
            const modelo = modelos.find((m) => m.id === metrica.modelo_id)
            return (
              <TableRow key={metrica.modelo_id}>
                <TableCell>
                  <span className="flex items-center gap-2 font-bold">
                    <span className="size-3 shrink-0 border-2" style={{ backgroundColor: modelo?.color }} />
                    {modelo?.nombre ?? metrica.modelo_id}
                  </span>
                </TableCell>
                <TableCell className="text-right">{entero(metrica.n)}</TableCell>
                {columnas.map((columna) => {
                  const destacado = metrica[columna.clave] !== null && metrica[columna.clave] === mejores[columna.clave]
                  return (
                    <TableCell key={columna.clave} className={cn("text-right", destacado && "bg-accent/50 font-bold")}>
                      {columna.formato(metrica)}
                    </TableCell>
                  )
                })}
                <TableCell className="text-right">{duracion(metrica.tiempo_entrenamiento_s)}</TableCell>
              </TableRow>
            )
          })}
        </TableBody>
      </Table>
    </div>
  )
}

function ResumenMetricas({ alcance, modelos }: { alcance: Alcance; modelos: ModeloColor[] }) {
  const consulta = useMetricas(alcance)
  return (
    <Contenido consulta={consulta} esVacio={(datos) => datos.length === 0} mensajeVacio="Ningún modelo tiene resultados de prueba.">
      {(datos) => {
        const metricas = datos.filter((m) => modelos.some((modelo) => modelo.id === m.modelo_id))
        if (metricas.length === 0) return <Vacio titulo="Sin métricas" descripcion="El modelo elegido no tiene resultados de prueba." />
        if (metricas.length === 1) {
          const [m] = metricas
          return (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <Metrica etiqueta="MAE" valor={numero(m.mae, 2)} detalle="Puntos de magnitud" className="bg-accent" />
              <Metrica etiqueta="RMSE" valor={numero(m.rmse, 2)} detalle="Penaliza errores grandes" />
              <Metrica etiqueta="R²" valor={numero(m.r2, 3)} detalle="Varianza explicada" />
              <Metrica etiqueta="Inferencia" valor={`${numero(m.tiempo_inferencia_ms, 3)} ms`} detalle={`Entrenamiento: ${duracion(m.tiempo_entrenamiento_s)}`} />
            </div>
          )
        }
        const filas = metricas.map((m) => ({
          modelo: modelos.find((modelo) => modelo.id === m.modelo_id)?.nombre ?? m.modelo_id,
          mae: m.mae,
          rmse: m.rmse,
        }))
        return (
          <div className="grid gap-6">
            <TablaMetricas metricas={metricas} modelos={modelos} />
            <GraficoBarras
              datos={filas}
              categoria="modelo"
              series={[
                { clave: "mae", nombre: "MAE", color: colorSerie(0) },
                { clave: "rmse", nombre: "RMSE", color: colorSerie(1) },
              ]}
              horizontal
              alto={Math.max(240, filas.length * 52)}
              anchoCategoria={270}
              formato={(v) => numero(v, 1)}
              etiquetaX="Error, en puntos de magnitud"
            />
          </div>
        )
      }}
    </Contenido>
  )
}

function histogramaResiduos(puntos: PuntoPrediccion[]) {
  const bordes = Array.from({ length: 22 }, (_, i) => -105 + i * 10)
  const conteos = bordes.slice(0, -1).map(() => 0)
  for (const punto of puntos) {
    const indice = Math.min(conteos.length - 1, Math.max(0, Math.floor((punto.error + 105) / 10)))
    conteos[indice] += 1
  }
  return conteos
}

function Predicciones({ alcance, modelos }: { alcance: Alcance; modelos: ModeloColor[] }) {
  const resultado = porModelo(usePredicciones(modelos.map((m) => m.id), alcance), modelos)
  if (resultado.isPending) return <Cargando alto="h-96" />
  if (resultado.disponibles.length === 0) return <AvisoError error={resultado.fallidos[0]?.error} />
  const disponibles = resultado.disponibles
  if (disponibles.every(({ datos }) => datos.length === 0)) {
    return (
      <div className="flex flex-col gap-4">
        <NotaFallidos fallidos={resultado.fallidos} />
        <Vacio titulo="Sin predicciones" descripcion="No hay registros de prueba para este alcance." />
      </div>
    )
  }
  const grupos = disponibles.map(({ modelo, datos }) => ({
    nombre: modelo.nombre,
    color: modelo.color,
    puntos: datos.map((p) => ({ x: p.real, y: p.predicho })),
  }))
  const residuos = disponibles.map(({ modelo, datos }) => ({ modelo, conteos: histogramaResiduos(datos) }))
  const filasResiduos: FilaGrafico[] = residuos[0].conteos.map((_, indice) => {
    const fila: FilaGrafico = { error: String(-100 + indice * 10) }
    for (const { modelo, conteos } of residuos) fila[modelo.id] = conteos[indice]
    return fila
  })
  return (
    <div className="flex flex-col gap-4">
      <NotaFallidos fallidos={resultado.fallidos} />
      <div className="grid gap-6 xl:grid-cols-2">
        <div>
          <h3 className="mb-1 font-head">Real contra predicho</h3>
          <p className="mb-3 text-sm text-muted-foreground">La diagonal punteada es la predicción perfecta.</p>
          <GraficoDispersion grupos={grupos} etiquetaX="Magnitud real" etiquetaY="Magnitud predicha" diagonal={[0, 100]} dominio={[0, 100]} alto={380} />
        </div>
        <div>
          <h3 className="mb-1 font-head">Distribución del error</h3>
          <p className="mb-3 text-sm text-muted-foreground">Predicho menos real. A la derecha del cero el modelo sobreestima.</p>
          <GraficoBarras
            datos={filasResiduos}
            categoria="error"
            series={disponibles.map(({ modelo }) => ({ clave: modelo.id, nombre: modelo.nombre, color: modelo.color }))}
            alto={380}
            formato={(v) => entero(v)}
            etiquetaX="Error, centro del intervalo"
            etiquetaY="Registros"
          />
        </div>
      </div>
    </div>
  )
}

function ErroresPorGrupo({ alcance, modelos }: { alcance: Alcance; modelos: ModeloColor[] }) {
  const [por, setPor] = useState<AgrupacionError>("temporada")
  const [medida, setMedida] = useState<"mae" | "rmse">("mae")
  const resultado = porModelo(useErrores(modelos.map((m) => m.id), por, alcance), modelos)

  let contenido
  if (resultado.isPending) contenido = <Cargando alto="h-80" />
  else if (resultado.disponibles.length === 0) contenido = <AvisoError error={resultado.fallidos[0]?.error} />
  else {
    const disponibles = resultado.disponibles
    const grupos = new Map<string, { grupo: string; etiqueta: string; n: number }>()
    for (const { datos } of disponibles) {
      for (const grupo of datos) if (!grupos.has(grupo.grupo)) grupos.set(grupo.grupo, grupo)
    }
    const filas = [...grupos.values()].map((grupo) => {
      const fila: FilaGrafico = { grupo: grupo.etiqueta }
      for (const { modelo, datos } of disponibles) {
        fila[modelo.id] = datos.find((g) => g.grupo === grupo.grupo)?.[medida] ?? null
      }
      return fila
    })
    contenido = (
      <>
        {filas.length === 0 ? (
          <Vacio titulo="Sin grupos" />
        ) : (
          <>
            <GraficoBarras
              datos={filas}
              categoria="grupo"
              series={disponibles.map(({ modelo }) => ({ clave: modelo.id, nombre: modelo.nombre, color: modelo.color }))}
              formato={(v) => numero(v, 1)}
              etiquetaY={medida.toUpperCase()}
            />
            <p className="text-xs text-muted-foreground">
              Registros por grupo: {[...grupos.values()].map((g) => `${g.etiqueta} ${entero(g.n)}`).join(", ")}.
            </p>
          </>
        )}
      </>
    )
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-end gap-4">
        <Selector etiqueta="Agrupar por" valor={por} onCambio={setPor} opciones={AGRUPACIONES} />
        <Alternador
          etiqueta="Medida de error"
          valor={medida}
          onCambio={setMedida}
          opciones={[
            { valor: "mae", etiqueta: "MAE" },
            { valor: "rmse", etiqueta: "RMSE" },
          ]}
        />
      </div>
      {contenido}
      <NotaFallidos fallidos={resultado.fallidos} />
    </div>
  )
}

function Paneles({ modelos }: { modelos: ModeloColor[] }) {
  const [seleccion] = useModeloSeleccionado()
  const [alcance, setAlcance] = useState<Alcance>("dr")
  const filtrados = filtrarSeleccion(modelos, seleccion, (modelo) => modelo.id)
  const visibles = filtrados.length > 0 ? filtrados : modelos
  const descripcionAlcance =
    alcance === "dr"
      ? "Registros de prueba con diagnóstico de sequía."
      : "Todo el conjunto de prueba; los diagnósticos distintos de sequía reciben 0 por regla."
  return (
    <div className="grid gap-6">
      <div className="flex flex-wrap items-center gap-3">
        <Alternador etiqueta="Alcance de la evaluación" valor={alcance} onCambio={setAlcance} opciones={ALCANCES} />
        <span className="text-sm text-muted-foreground">{descripcionAlcance}</span>
      </div>
      <Bloque titulo="Métricas de prueba" descripcion="El mejor valor de cada columna aparece resaltado.">
        <ResumenMetricas alcance={alcance} modelos={visibles} />
      </Bloque>
      <Bloque titulo="Predicciones" descripcion="Cada punto es una fotografía del conjunto de prueba.">
        <Predicciones alcance={alcance} modelos={visibles} />
      </Bloque>
      <Bloque titulo="Error por grupo" descripcion="Dónde se equivoca más cada modelo.">
        <ErroresPorGrupo alcance={alcance} modelos={visibles} />
      </Bloque>
    </div>
  )
}

export default function Rendimiento() {
  const modelos = useModelos()
  const conResultados = (modelos.data ?? [])
    .map((modelo, i) => ({ ...modelo, color: colorSerie(i) }))
    .filter((modelo) => modelo.tiene_resultados)
  return (
    <>
      <Encabezado
        etiqueta="Requisito c"
        titulo="Rendimiento"
        descripcion="Efectividad de los modelos sobre el conjunto de prueba, errores por grupo y tiempos de entrenamiento e inferencia."
      >
        {conResultados.length > 0 && <SelectorModelos modelos={conResultados} />}
      </Encabezado>
      <Contenido
        consulta={modelos}
        alto="h-96"
        esVacio={() => conResultados.length === 0}
        mensajeVacio="Ningún modelo tiene resultados de prueba. Entrene un modelo y guarde sus resultados en data/procesado/resultados/."
      >
        {() => <Paneles modelos={conResultados} />}
      </Contenido>
    </>
  )
}
