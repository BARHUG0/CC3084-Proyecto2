import { colorMagnitud, etiquetaMagnitud } from "@/lib/colores"

const PASOS = Array.from({ length: 11 }, (_, i) => i * 10)

export function EscalaMagnitud() {
  return (
    <figure className="flex flex-col gap-2">
      <div className="flex border-2 shadow-sm" role="img" aria-label="Escala de color de la magnitud del daño de 0 a 100">
        {PASOS.map((paso) => (
          <div key={paso} className="h-8 flex-1" style={{ backgroundColor: colorMagnitud(paso) }} />
        ))}
      </div>
      <div className="flex justify-between text-xs font-bold">
        {PASOS.filter((paso) => paso % 20 === 0).map((paso) => (
          <span key={paso}>{paso}</span>
        ))}
      </div>
      <figcaption className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted-foreground">
        {[10, 35, 65, 90].map((valor) => (
          <span key={valor} className="flex items-center gap-1.5">
            <span className="size-3 border-2" style={{ backgroundColor: colorMagnitud(valor) }} />
            {etiquetaMagnitud(valor)}
          </span>
        ))}
      </figcaption>
    </figure>
  )
}
