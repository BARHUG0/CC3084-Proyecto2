import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts"

import type { FilaGrafico } from "@/components/graficos/GraficoBarras"
import { TooltipNeo } from "@/components/graficos/TooltipNeo"
import { EJE, etiquetaEje, LEYENDA, REJILLA, useSeriesOcultas, type Serie } from "@/components/graficos/tema"

export function GraficoLineas({
  datos,
  categoria,
  series,
  etiquetaX,
  etiquetaY,
  alto = 280,
}: {
  datos: FilaGrafico[]
  categoria: string
  series: Serie[]
  etiquetaX: string
  etiquetaY: string
  alto?: number
}) {
  const { ocultas, alternar } = useSeriesOcultas()
  return (
    <ResponsiveContainer width="100%" height={alto}>
      <LineChart data={datos} margin={{ top: 8, right: 16, bottom: 24, left: 16 }}>
        <CartesianGrid {...REJILLA} />
        <XAxis {...EJE} dataKey={categoria} label={etiquetaEje(etiquetaX)} />
        <YAxis {...EJE} label={etiquetaEje(etiquetaY, true)} />
        <Tooltip content={<TooltipNeo formato={(valor) => valor.toFixed(4)} />} />
        <Legend {...LEYENDA} onClick={(entrada) => alternar(entrada.dataKey)} />
        {series.map((serie) => (
          <Line
            key={serie.clave}
            dataKey={serie.clave}
            name={serie.nombre}
            stroke={serie.color}
            strokeWidth={3}
            dot={{ r: 4, stroke: "#000", strokeWidth: 2, fill: serie.color }}
            hide={ocultas.has(serie.clave)}
            connectNulls
            isAnimationActive={false}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  )
}
