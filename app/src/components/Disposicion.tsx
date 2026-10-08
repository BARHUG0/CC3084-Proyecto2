import { Sprout } from "lucide-react"
import { NavLink, Outlet, useSearchParams } from "react-router"

import { useSalud } from "@/api/consultas"
import { SECCIONES } from "@/components/navegacion"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"

function IndicadorSalud() {
  const { data: salud, isError, isPending } = useSalud()
  if (isPending) return <Badge variant="outline">Conectando</Badge>
  if (isError) return <Badge variant="destructive">API sin conexión</Badge>
  if (!salud.datos_disponibles) return <Badge variant="secondary">API sin datos</Badge>
  return <Badge>API v{salud.version}</Badge>
}

export function Disposicion() {
  const [parametros] = useSearchParams()
  const busqueda = parametros.toString()
  return (
    <div className="flex min-h-svh flex-col">
      <header className="sticky top-0 z-40 border-b-4 bg-background">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-x-6 gap-y-3 px-4 py-3">
          <NavLink to="/" className="flex items-center gap-2">
            <span className="flex size-10 items-center justify-center border-2 bg-primary text-primary-foreground shadow-sm">
              <Sprout className="size-6" />
            </span>
            <span className="font-head text-lg leading-tight">
              Ojos en el campo
              <span className="block font-sans text-xs font-medium text-muted-foreground">Daño por sequía en cultivos</span>
            </span>
          </NavLink>
          <nav className="flex flex-1 flex-wrap gap-2">
            {SECCIONES.map(({ ruta, titulo, icono: Icono }) => (
              <NavLink
                key={ruta}
                to={busqueda ? `${ruta}?${busqueda}` : ruta}
                end={ruta === "/"}
                className={({ isActive }) =>
                  cn(
                    "flex items-center gap-1.5 border-2 px-3 py-1.5 font-head text-sm transition-all",
                    isActive
                      ? "bg-secondary shadow-md"
                      : "border-transparent hover:border-border hover:bg-card hover:shadow-sm",
                  )
                }
              >
                <Icono className="size-4" />
                {titulo}
              </NavLink>
            ))}
          </nav>
          <IndicadorSalud />
        </div>
      </header>
      <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-8">
        <Outlet />
      </main>
      <footer className="border-t-4 bg-foreground py-4 text-center text-sm text-background">
        CC3084 Data Science - CGIAR Eyes on the Ground
      </footer>
    </div>
  )
}
