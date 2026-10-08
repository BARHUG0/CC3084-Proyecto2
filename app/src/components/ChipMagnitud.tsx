import { colorMagnitud } from "@/lib/colores"
import { numero } from "@/lib/formato"

export function ChipMagnitud({ valor, decimales = 0 }: { valor: number; decimales?: number }) {
  return (
    <span className="inline-flex items-center gap-2 font-bold tabular-nums">
      <span className="size-3.5 shrink-0 border-2" style={{ backgroundColor: colorMagnitud(valor) }} />
      {numero(valor, decimales)}
    </span>
  )
}
