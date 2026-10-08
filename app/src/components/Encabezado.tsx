import type { ReactNode } from "react"

export function Encabezado({
  titulo,
  descripcion,
  etiqueta,
  children,
}: {
  titulo: string
  descripcion: string
  etiqueta?: string
  children?: ReactNode
}) {
  return (
    <div className="mb-8 flex flex-wrap items-end justify-between gap-4 border-b-4 pb-6">
      <div className="max-w-3xl">
        {etiqueta && (
          <span className="mb-2 inline-block border-2 bg-secondary px-2 py-0.5 font-head text-xs uppercase shadow-sm">
            {etiqueta}
          </span>
        )}
        <h1 className="text-3xl md:text-4xl">{titulo}</h1>
        <p className="mt-2 text-base text-muted-foreground">{descripcion}</p>
      </div>
      {children && <div className="flex flex-wrap items-center gap-3">{children}</div>}
    </div>
  )
}
