import { useEffect } from "react"

import type { ModeloInfo } from "@/api/cliente"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { TODOS, useModeloSeleccionado } from "@/lib/seleccion"

export function SelectorModelos({ modelos }: { modelos: Pick<ModeloInfo, "id" | "nombre">[] }) {
  const [seleccion, setSeleccion] = useModeloSeleccionado()
  const valida = seleccion === TODOS || modelos.some((m) => m.id === seleccion)
  const valor = valida ? seleccion : TODOS
  useEffect(() => {
    if (!valida) setSeleccion(TODOS)
  }, [valida, setSeleccion])
  return (
    <div className="flex items-center gap-2">
      <Label htmlFor="selector-modelos" className="font-head">
        Modelo
      </Label>
      <Select value={valor} onValueChange={setSeleccion}>
        <SelectTrigger id="selector-modelos" className="min-w-52 bg-card">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value={TODOS}>Todos los modelos</SelectItem>
          {modelos.map((modelo) => (
            <SelectItem key={modelo.id} value={modelo.id}>
              {modelo.nombre}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  )
}
