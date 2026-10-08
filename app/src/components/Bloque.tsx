import type { ReactNode } from "react"

import { Card, CardAction, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { cn } from "@/lib/utils"

export function Bloque({
  titulo,
  descripcion,
  acciones,
  className,
  children,
}: {
  titulo: string
  descripcion?: string
  acciones?: ReactNode
  className?: string
  children: ReactNode
}) {
  return (
    <Card className={cn("gap-4", className)}>
      <CardHeader>
        <CardTitle className="font-head text-lg">{titulo}</CardTitle>
        {descripcion && <CardDescription>{descripcion}</CardDescription>}
        {acciones && <CardAction className="flex flex-wrap items-center justify-end gap-3">{acciones}</CardAction>}
      </CardHeader>
      <CardContent>{children}</CardContent>
    </Card>
  )
}
