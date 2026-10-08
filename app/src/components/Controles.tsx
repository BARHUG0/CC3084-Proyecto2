import { useId } from "react"

import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group"
import { cn } from "@/lib/utils"

export type OpcionControl<T extends string> = { valor: T; etiqueta: string }

export function Selector<T extends string>({
  etiqueta,
  valor,
  opciones,
  onCambio,
  className,
}: {
  etiqueta: string
  valor: T
  opciones: OpcionControl<T>[]
  onCambio: (valor: T) => void
  className?: string
}) {
  const id = useId()
  return (
    <div className={cn("flex flex-col gap-1.5", className)}>
      <Label htmlFor={id} className="text-xs font-bold uppercase">
        {etiqueta}
      </Label>
      <Select value={valor} onValueChange={(nuevo) => onCambio(nuevo as T)}>
        <SelectTrigger id={id} className="min-w-40 bg-card">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {opciones.map((opcion) => (
            <SelectItem key={opcion.valor} value={opcion.valor}>
              {opcion.etiqueta}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  )
}

export function Interruptor({
  etiqueta,
  activo,
  onCambio,
}: {
  etiqueta: string
  activo: boolean
  onCambio: (activo: boolean) => void
}) {
  const id = useId()
  return (
    <div className="flex items-center gap-2">
      <Switch id={id} checked={activo} onCheckedChange={onCambio} />
      <Label htmlFor={id} className="cursor-pointer text-sm font-bold">
        {etiqueta}
      </Label>
    </div>
  )
}

export function Alternador<T extends string>({
  valor,
  opciones,
  onCambio,
  etiqueta,
}: {
  valor: T
  opciones: OpcionControl<T>[]
  onCambio: (valor: T) => void
  etiqueta: string
}) {
  return (
    <ToggleGroup
      type="single"
      variant="outline"
      value={valor}
      onValueChange={(nuevo) => nuevo && onCambio(nuevo as T)}
      aria-label={etiqueta}
    >
      {opciones.map((opcion) => (
        <ToggleGroupItem key={opcion.valor} value={opcion.valor} className="px-3 font-head text-xs">
          {opcion.etiqueta}
        </ToggleGroupItem>
      ))}
    </ToggleGroup>
  )
}
