import {
  CartesianGrid,
  ReferenceLine,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts"

import { LeyendaSeries } from "@/components/graficos/LeyendaSeries"
import { TooltipNeo } from "@/components/graficos/TooltipNeo"
import { EJE, etiquetaEje, REJILLA, useSeriesOcultas } from "@/components/graficos/tema"
import { PALETA } from "@/lib/colores"

export type GrupoPuntos = { nombre: string; color: string; puntos: { x: number; y: number }[] }

const FORMAS = ["circle", "triangle", "square", "diamond", "cross", "star", "wye", "circle"] as const

export function GraficoDispersion({
  grupos,
  etiquetaX,
  etiquetaY,
  alto = 340,
  diagonal,
  dominio,
}: {
  grupos: GrupoPuntos[]
  etiquetaX: string
  etiquetaY: string
  alto?: number
  diagonal?: [number, number]
  dominio?: [number, number]
}) {
  const { ocultas, alternar } = useSeriesOcultas()
  const series = grupos.map((grupo) => ({ clave: grupo.nombre, nombre: grupo.nombre, color: grupo.color }))
  return (
    <div>
      <ResponsiveContainer width="100%" height={alto}>
        <ScatterChart margin={{ top: 8, right: 16, bottom: 24, left: 16 }}>
          <CartesianGrid {...REJILLA} />
          <XAxis {...EJE} type="number" dataKey="x" name={etiquetaX} domain={dominio ?? ["auto", "auto"]} label={etiquetaEje(etiquetaX)} />
          <YAxis {...EJE} type="number" dataKey="y" name={etiquetaY} domain={dominio ?? ["auto", "auto"]} label={etiquetaEje(etiquetaY, true)} />
          <ZAxis range={[28, 28]} />
          <Tooltip content={<TooltipNeo />} cursor={{ stroke: PALETA.tinta, strokeDasharray: "3 3" }} />
          {diagonal && (
            <ReferenceLine
              segment={[
                { x: diagonal[0], y: diagonal[0] },
                { x: diagonal[1], y: diagonal[1] },
              ]}
              stroke={PALETA.tinta}
              strokeWidth={2}
              strokeDasharray="6 4"
              ifOverflow="extendDomain"
            />
          )}
          {grupos.map((grupo, indice) => (
            <Scatter
              key={grupo.nombre}
              name={grupo.nombre}
              data={grupo.puntos}
              fill={grupo.color}
              fillOpacity={0.7}
              stroke={PALETA.tinta}
              strokeWidth={1}
              shape={FORMAS[indice % FORMAS.length]}
              hide={ocultas.has(grupo.nombre)}
              isAnimationActive={false}
            />
          ))}
        </ScatterChart>
      </ResponsiveContainer>
      <LeyendaSeries series={series} ocultas={ocultas} onAlternar={alternar} />
    </div>
  )
}
