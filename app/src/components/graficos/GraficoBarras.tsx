import { Bar, BarChart, Brush, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts"

import { LeyendaSeries } from "@/components/graficos/LeyendaSeries"
import { TooltipNeo } from "@/components/graficos/TooltipNeo"
import { BORDE_BARRA, EJE, etiquetaEje, REJILLA, useSeriesOcultas, type Serie } from "@/components/graficos/tema"
import { PALETA } from "@/lib/colores"

export type FilaGrafico = Record<string, string | number | null>

export function GraficoBarras({
  datos,
  categoria,
  series,
  alto = 300,
  horizontal = false,
  apilado = false,
  zoom = false,
  colorBarra,
  formato,
  etiquetaX,
  etiquetaY,
  anchoCategoria = 140,
}: {
  datos: FilaGrafico[]
  categoria: string
  series: Serie[]
  alto?: number
  horizontal?: boolean
  apilado?: boolean
  zoom?: boolean
  colorBarra?: (fila: FilaGrafico, serie: Serie) => string
  formato?: (valor: number) => string
  etiquetaX?: string
  etiquetaY?: string
  anchoCategoria?: number
}) {
  const { ocultas, alternar } = useSeriesOcultas()
  const conBrush = zoom && datos.length > 12
  const etiquetaCategoria = etiquetaX && { ...etiquetaEje(etiquetaX), offset: conBrush ? 2 : -10 }
  const ejeCategoria = { ...EJE, dataKey: categoria, type: "category" as const, interval: datos.length > 12 ? ("preserveStartEnd" as const) : 0, minTickGap: 12 }
  const ejeValor = { ...EJE, type: "number" as const, tickFormatter: formato }

  return (
    <div>
      <ResponsiveContainer width="100%" height={alto}>
        <BarChart
          data={datos}
          layout={horizontal ? "vertical" : "horizontal"}
          margin={{ top: 8, right: 16, bottom: etiquetaX ? 24 : 8, left: etiquetaY ? 16 : 0 }}
        >
          <CartesianGrid {...REJILLA} vertical={horizontal} horizontal={!horizontal} />
          {horizontal ? (
            <>
              <XAxis {...ejeValor} label={etiquetaX ? etiquetaEje(etiquetaX) : undefined} />
              <YAxis {...ejeCategoria} width={anchoCategoria} />
            </>
          ) : (
            <>
              <XAxis {...ejeCategoria} height={conBrush ? 46 : 30} label={etiquetaCategoria || undefined} />
              <YAxis {...ejeValor} label={etiquetaY ? etiquetaEje(etiquetaY, true) : undefined} />
            </>
          )}
          <Tooltip content={<TooltipNeo formato={formato} />} cursor={{ fill: PALETA.tinta, fillOpacity: 0.06 }} />
          {series.map((serie) => (
            <Bar
              key={serie.clave}
              dataKey={serie.clave}
              name={serie.nombre}
              fill={serie.color}
              stackId={apilado ? "pila" : undefined}
              hide={ocultas.has(serie.clave)}
              isAnimationActive={false}
              {...BORDE_BARRA}
            >
              {colorBarra && datos.map((fila, indice) => <Cell key={indice} fill={colorBarra(fila, serie)} />)}
            </Bar>
          ))}
          {conBrush && (
            <Brush dataKey={categoria} height={24} stroke={PALETA.tinta} fill={PALETA.fondo} travellerWidth={10} ariaLabel="Rango visible del gráfico" />
          )}
        </BarChart>
      </ResponsiveContainer>
      <LeyendaSeries series={series} ocultas={ocultas} onAlternar={alternar} />
    </div>
  )
}
