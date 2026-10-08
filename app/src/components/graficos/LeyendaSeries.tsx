import type { Serie } from "@/components/graficos/tema"
import { cn } from "@/lib/utils"

export function LeyendaSeries({
  series,
  ocultas,
  onAlternar,
}: {
  series: { clave: string; nombre: string; color: string }[]
  ocultas: Set<string>
  onAlternar: (clave: string) => void
}) {
  if (series.length <= 1) return null
  return (
    <ul className="flex flex-wrap items-center justify-center gap-x-4 gap-y-1 pt-2 text-[13px]">
      {series.map((serie: Serie) => {
        const oculta = ocultas.has(serie.clave)
        return (
          <li key={serie.clave}>
            <button
              type="button"
              aria-pressed={!oculta}
              aria-label={`${oculta ? "Mostrar" : "Ocultar"} ${serie.nombre}`}
              onClick={() => onAlternar(serie.clave)}
              className={cn(
                "flex items-center gap-1.5 border-2 border-transparent px-1.5 py-0.5 hover:border-border hover:bg-card",
                "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary",
                oculta && "opacity-45",
              )}
            >
              <span className="size-3 border-2" style={{ backgroundColor: serie.color }} />
              <span className={cn(oculta && "line-through")}>{serie.nombre}</span>
            </button>
          </li>
        )
      })}
    </ul>
  )
}
