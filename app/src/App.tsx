import { Button } from "@/components/ui/button"
import { colorMagnitud } from "@/lib/colores"

export default function App() {
  return (
    <main className="mx-auto flex max-w-3xl flex-col gap-6 p-8">
      <h1 className="text-4xl">Ojos en el campo</h1>
      <div className="flex gap-1">
        {Array.from({ length: 11 }, (_, i) => i * 10).map((magnitud) => (
          <div
            key={magnitud}
            className="flex h-12 flex-1 items-end border-2 p-1 text-xs font-bold text-white"
            style={{ backgroundColor: colorMagnitud(magnitud) }}
          >
            {magnitud}
          </div>
        ))}
      </div>
      <Button className="w-fit">Comenzar</Button>
    </main>
  )
}
