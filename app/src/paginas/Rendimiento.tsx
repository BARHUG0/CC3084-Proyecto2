import { useState } from "react"
import type { UseQueryResult } from "@tanstack/react-query"

import type { AgrupacionError, Alcance, ErrorGrupo, Metricas, ModeloInfo, PuntoPrediccion } from "@/api/cliente"
import { useErrores, useMetricas, useModelos, usePredicciones } from "@/api/consultas"
import { Bloque } from "@/components/Bloque"
import { Alternador, Selector } from "@/components/Controles"
import { Encabezado } from "@/components/Encabezado"
import { AvisoError, Cargando, Contenido, Vacio } from "@/components/Estados"
import { GraficoBarras, type FilaGrafico } from "@/components/graficos/GraficoBarras"
import { GraficoDispersion } from "@/components/graficos/GraficoDispersion"
import { Metrica } from "@/components/Metrica"
import { SelectorModelos } from "@/components/SelectorModelos"
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

function combinar<T>(consultas: UseQueryResult<T>[]) {
  return {
    isPending: consultas.some((consulta) => consulta.isPending),
    error: consultas.find((consulta) => consulta.error)?.error ?? null,
    data: consultas.every((consulta) => consulta.data !== undefined) ? consultas.map((consulta) => consulta.data as T) : undefined,
  }
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
                  const destacado = metrica[columna.clave] !== null && metrica[columna.clave] === mejor(metricas, columna.clave)
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
          <div className="grid gap-6 xl:grid-cols-[3fr_2fr]">
            <TablaMetricas metricas={metricas} modelos={modelos} />
            <GraficoBarras
              datos={filas}
              categoria="modelo"
              series={[
                { clave: "mae", nombre: "MAE", color: colorSerie(0) },
                { clave: "rmse", nombre: "RMSE", color: colorSerie(1) },
              ]}
              formato={(v) => numero(v, 1)}
              etiquetaY="Error"
            />
          </div>
        )
      }}
    </Contenido>
  )
}

function histogramaResiduos(puntos: PuntoPrediccion[]) {
  const bordes = Array.from({ length: 21 }, (_, i) => -100 + i * 10)
  const conteos = bordes.slice(0, -1).map(() => 0)
  for (const punto of puntos) {
    const indice = Math.min(conteos.length - 1, Math.max(0, Math.floor((punto.error + 100) / 10)))
    conteos[indice] += 1
  }
  return conteos
}

function Predicciones({ alcance, modelos }: { alcance: Alcance; modelos: ModeloColor[] }) {
  const consulta = combinar(usePredicciones(modelos.map((m) => m.id), alcance))
  if (consulta.isPending) return <Cargando alto="h-96" />
  if (!consulta.data) return <AvisoError error={consulta.error} />
  const respuestas = consulta.data
  const grupos = modelos.map((modelo, i) => ({
    nombre: modelo.nombre,
    color: modelo.color,
    puntos: respuestas[i].map((p) => ({ x: p.real, y: p.predicho })),
  }))
  const residuos = modelos.map((modelo, i) => ({ modelo, conteos: histogramaResiduos(respuestas[i]) }))
  const filasResiduos: FilaGrafico[] = residuos[0].conteos.map((_, indice) => {
    const fila: FilaGrafico = { error: String(-95 + indice * 10) }
    for (const { modelo, conteos } of residuos) fila[modelo.id] = conteos[indice]
    return fila
  })
  return (
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
          series={modelos.map((m) => ({ clave: m.id, nombre: m.nombre, color: m.color }))}
          alto={380}
          formato={(v) => entero(v)}
          etiquetaX="Error, centro del intervalo"
          etiquetaY="Registros"
        />
      </div>
    </div>
  )
}

function ErroresPorGrupo({ alcance, modelos }: { alcance: Alcance; modelos: ModeloColor[] }) {
  const [por, setPor] = useState<AgrupacionError>("temporada")
  const [medida, setMedida] = useState<"mae" | "rmse">("mae")
  const consulta = combinar(useErrores(modelos.map((m) => m.id), por, alcance))

  let contenido
  if (consulta.isPending) contenido = <Cargando alto="h-80" />
  else if (!consulta.data) contenido = <AvisoError error={consulta.error} />
  else {
    const respuestas: ErrorGrupo[][] = consulta.data
    const grupos = respuestas[0] ?? []
    const filas = grupos.map((grupo) => {
      const fila: FilaGrafico = { grupo: grupo.etiqueta }
      modelos.forEach((modelo, i) => {
        fila[modelo.id] = respuestas[i].find((g) => g.grupo === grupo.grupo)?.[medida] ?? null
      })
      return fila
    })
    contenido =
      filas.length === 0 ? (
        <Vacio titulo="Sin grupos" />
      ) : (
        <>
          <GraficoBarras
            datos={filas}
            categoria="grupo"
            series={modelos.map((m) => ({ clave: m.id, nombre: m.nombre, color: m.color }))}
            formato={(v) => numero(v, 1)}
            etiquetaY={medida.toUpperCase()}
          />
          <p className="text-xs text-muted-foreground">
            Registros por grupo: {grupos.map((g) => `${g.etiqueta} ${entero(g.n)}`).join(", ")}.
          </p>
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
