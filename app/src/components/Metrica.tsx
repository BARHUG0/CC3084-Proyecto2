import type { ReactNode } from "react"

import { cn } from "@/lib/utils"

export function Metrica({
  etiqueta,
  valor,
  detalle,
  className,
}: {
  etiqueta: string
  valor: ReactNode
  detalle?: ReactNode
  className?: string
}) {
  return (
    <div className={cn("flex flex-col gap-1 border-2 bg-card p-4 shadow-md", className)}>
      <span className="text-xs font-bold tracking-wide text-muted-foreground uppercase">{etiqueta}</span>
      <span className="font-head text-3xl">{valor}</span>
      {detalle && <span className="text-sm text-muted-foreground">{detalle}</span>}
    </div>
  )
}
