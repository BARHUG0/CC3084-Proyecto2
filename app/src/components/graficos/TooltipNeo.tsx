import type { TooltipContentProps } from "recharts"

import { numero } from "@/lib/formato"

export type PropsTooltip = Partial<TooltipContentProps<number, string>> & { formato?: (valor: number) => string }

export function TooltipNeo({ active, payload, label, formato = (valor) => numero(valor, 2) }: PropsTooltip) {
  if (!active || !payload?.length) return null
  return (
    <div className="border-2 bg-card px-3 py-2 text-sm shadow-md">
      {label !== undefined && label !== "" && <p className="mb-1 font-head">{label}</p>}
      {payload.map((elemento, indice) => (
        <p key={`${String(elemento.dataKey ?? elemento.name)}-${indice}`} className="flex items-center gap-2">
          <span className="size-3 border-2" style={{ backgroundColor: elemento.color ?? elemento.payload?.fill }} />
          <span>{elemento.name}:</span>
          <span className="font-bold">{typeof elemento.value === "number" ? formato(elemento.value) : elemento.value}</span>
        </p>
      ))}
    </div>
  )
}
