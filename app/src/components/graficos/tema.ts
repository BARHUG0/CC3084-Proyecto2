import { useState } from "react"

import { PALETA } from "@/lib/colores"

export const TICK = { fill: PALETA.tinta, fontSize: 12, fontFamily: "Space Grotesk" }
export const EJE = { stroke: PALETA.tinta, strokeWidth: 2, tick: TICK, tickLine: { stroke: PALETA.tinta } }
export const REJILLA = { stroke: PALETA.tinta, strokeOpacity: 0.12, strokeDasharray: "4 4" }
export const LEYENDA = { wrapperStyle: { fontFamily: "Space Grotesk", fontSize: 13, cursor: "pointer", paddingTop: 8 } }
export const BORDE_BARRA = { stroke: PALETA.tinta, strokeWidth: 2 }

export type Serie = { clave: string; nombre: string; color: string }

export function etiquetaEje(valor: string, vertical = false) {
  return {
    value: valor,
    angle: vertical ? -90 : 0,
    position: vertical ? ("insideLeft" as const) : ("insideBottom" as const),
    offset: vertical ? 10 : -10,
    style: { ...TICK, fontWeight: 700, textAnchor: "middle" as const },
  }
}

export function useSeriesOcultas() {
  const [ocultas, setOcultas] = useState<Set<string>>(new Set())
  const alternar = (clave: unknown) =>
    setOcultas((actuales) => {
      const siguientes = new Set(actuales)
      const texto = String(clave)
      if (siguientes.has(texto)) siguientes.delete(texto)
      else siguientes.add(texto)
      return siguientes
    })
  return { ocultas, alternar }
}
