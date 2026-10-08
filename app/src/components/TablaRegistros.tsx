import { useState } from "react"
import { ArrowDown, ArrowUp, ArrowUpDown, ChevronLeft, ChevronRight, MousePointerClick } from "lucide-react"

import { urlImagen, type FiltrosRegistros, type Registro } from "@/api/cliente"
import { useRegistros } from "@/api/consultas"
import { ChipMagnitud } from "@/components/ChipMagnitud"
import { Selector, type OpcionControl } from "@/components/Controles"
import { AvisoError, Cargando, Vacio } from "@/components/Estados"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import { Slider } from "@/components/ui/slider"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { ETIQUETAS_SUBCONJUNTO, useEtiquetas, useEtiquetasVariables } from "@/lib/catalogos"
import { entero, numero } from "@/lib/formato"
import { TODOS } from "@/lib/seleccion"
import { cn } from "@/lib/utils"

type CampoOrden = NonNullable<FiltrosRegistros["orden"]>
type Filtros = { temporada: string; dano: string; etapa: string; subconjunto: string }

const TAMANO_PAGINA = 12
const FILTROS_INICIALES: Filtros = { temporada: TODOS, dano: TODOS, etapa: TODOS, subconjunto: TODOS }

function opciones(lista: { codigo: string; nombre: string }[] | undefined, todos: string): OpcionControl<string>[] {
  return [{ valor: TODOS, etiqueta: todos }, ...(lista ?? []).map((o) => ({ valor: o.codigo, etiqueta: o.nombre }))]
}

function sinTodos(valor: string) {
  return valor === TODOS ? undefined : valor
}

function paginasVisibles(actual: number, total: number) {
  const inicio = Math.max(1, Math.min(actual - 2, total - 4))
  return Array.from({ length: Math.min(5, total) }, (_, i) => inicio + i)
}

function Columna({
  campo,
  titulo,
  orden,
  descendente,
  onOrdenar,
  className,
}: {
  campo: CampoOrden
  titulo: string
  orden: CampoOrden
  descendente: boolean
  onOrdenar: (campo: CampoOrden) => void
  className?: string
}) {
  const Icono = orden !== campo ? ArrowUpDown : descendente ? ArrowDown : ArrowUp
  return (
    <TableHead className={className} aria-sort={orden === campo ? (descendente ? "descending" : "ascending") : "none"}>
      <button type="button" onClick={() => onOrdenar(campo)} className="flex items-center gap-1 font-head hover:underline">
        {titulo}
        <Icono className={cn("size-3.5", orden !== campo && "opacity-40")} />
      </button>
    </TableHead>
  )
}

function DetalleRegistro({ registro, onCerrar }: { registro: Registro | null; onCerrar: () => void }) {
  const etiquetas = useEtiquetas()
  const etiquetaVariable = useEtiquetasVariables()
  const [fallida, setFallida] = useState<string | null>(null)
  return (
    <Dialog open={registro !== null} onOpenChange={(abierto) => !abierto && onCerrar()}>
      <DialogContent className="max-h-[90svh] overflow-y-auto sm:max-w-3xl">
        {registro && (
          <>
            <DialogHeader>
              <DialogTitle className="font-head">{registro.id}</DialogTitle>
              <DialogDescription>{registro.archivo}</DialogDescription>
            </DialogHeader>
            <div className="grid gap-5 md:grid-cols-[1.2fr_1fr]">
              {fallida === registro.id ? (
                <Vacio titulo="Fotografía no disponible" descripcion="La imagen no está descargada en el servidor." />
              ) : (
                <img
                  src={urlImagen(registro.id, 640)}
                  alt={`Fotografía del registro ${registro.id}`}
                  onError={() => setFallida(registro.id)}
                  className="aspect-4/3 w-full border-2 bg-muted object-cover shadow-md"
                />
              )}
              <dl className="grid grid-cols-2 content-start gap-x-4 gap-y-2 text-sm">
                <dt className="font-bold">Magnitud</dt>
                <dd>
                  <ChipMagnitud valor={registro.magnitud} />
                </dd>
                <dt className="font-bold">Daño</dt>
                <dd>{etiquetas.dano(registro.dano)}</dd>
                <dt className="font-bold">Temporada</dt>
                <dd>{registro.temporada}</dd>
                <dt className="font-bold">Etapa</dt>
                <dd>{etiquetas.etapa(registro.etapa)}</dd>
                <dt className="font-bold">Captura</dt>
                <dd>{etiquetas.captura(registro.tipo_captura)}</dd>
                <dt className="font-bold">Subconjunto</dt>
                <dd>{ETIQUETAS_SUBCONJUNTO[registro.subconjunto]}</dd>
                <dt className="col-span-2 mt-2 border-t-2 pt-2 font-head">Atributos de imagen</dt>
                {Object.entries(registro.atributos).map(([nombre, valor]) => (
                  <div key={nombre} className="contents">
                    <dt className="text-muted-foreground">{etiquetaVariable(nombre)}</dt>
                    <dd className="tabular-nums">{numero(valor, 3)}</dd>
                  </div>
                ))}
              </dl>
            </div>
          </>
        )}
      </DialogContent>
    </Dialog>
  )
}

export function TablaRegistros() {
  const etiquetas = useEtiquetas()
  const [filtros, setFiltros] = useState<Filtros>(FILTROS_INICIALES)
  const [rango, setRango] = useState<[number, number]>([0, 100])
  const [rangoConsulta, setRangoConsulta] = useState<[number, number]>([0, 100])
  const [orden, setOrden] = useState<CampoOrden>("id")
  const [descendente, setDescendente] = useState(false)
  const [pagina, setPagina] = useState(1)
  const [seleccionado, setSeleccionado] = useState<Registro | null>(null)

  const consulta = useRegistros({
    pagina,
    tamano: TAMANO_PAGINA,
    temporada: sinTodos(filtros.temporada) as FiltrosRegistros["temporada"],
    dano: sinTodos(filtros.dano) as FiltrosRegistros["dano"],
    etapa: sinTodos(filtros.etapa) as FiltrosRegistros["etapa"],
    subconjunto: sinTodos(filtros.subconjunto) as FiltrosRegistros["subconjunto"],
    magnitud_min: rangoConsulta[0] > 0 ? rangoConsulta[0] : undefined,
    magnitud_max: rangoConsulta[1] < 100 ? rangoConsulta[1] : undefined,
    orden,
    descendente,
  })

  const cambiarFiltro = (campo: keyof Filtros) => (valor: string) => {
    setFiltros((actuales) => ({ ...actuales, [campo]: valor }))
    setPagina(1)
  }

  const ordenar = (campo: CampoOrden) => {
    setDescendente(campo === orden ? !descendente : campo === "magnitud")
    setOrden(campo)
    setPagina(1)
  }

  const limpiar = () => {
    setFiltros(FILTROS_INICIALES)
    setRango([0, 100])
    setRangoConsulta([0, 100])
    setPagina(1)
  }

  const catalogos = etiquetas.catalogos
  const datos = consulta.data
  const columnas = { orden, descendente, onOrdenar: ordenar }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-end gap-4">
        <Selector etiqueta="Temporada" valor={filtros.temporada} onCambio={cambiarFiltro("temporada")} opciones={opciones(catalogos?.temporadas, "Todas")} />
        <Selector etiqueta="Daño" valor={filtros.dano} onCambio={cambiarFiltro("dano")} opciones={opciones(catalogos?.danos, "Todos")} />
        <Selector etiqueta="Etapa" valor={filtros.etapa} onCambio={cambiarFiltro("etapa")} opciones={opciones(catalogos?.etapas, "Todas")} />
        <Selector
          etiqueta="Subconjunto"
          valor={filtros.subconjunto}
          onCambio={cambiarFiltro("subconjunto")}
          opciones={opciones(Object.entries(ETIQUETAS_SUBCONJUNTO).map(([codigo, nombre]) => ({ codigo, nombre })), "Todos")}
        />
        <div className="flex min-w-56 flex-1 flex-col gap-3">
          <Label className="text-xs font-bold uppercase">
            Magnitud entre {rango[0]} y {rango[1]}
          </Label>
          <Slider
            value={rango}
            min={0}
            max={100}
            step={10}
            minStepsBetweenThumbs={0}
            onValueChange={(valor) => setRango([valor[0], valor[1]])}
            onValueCommit={(valor) => {
              setRangoConsulta([valor[0], valor[1]])
              setPagina(1)
            }}
            aria-label="Rango de magnitud"
          />
        </div>
        <Button variant="outline" onClick={limpiar}>
          Limpiar filtros
        </Button>
      </div>

      {consulta.isPending && <Cargando alto="h-96" />}
      {!consulta.isPending && !datos && <AvisoError error={consulta.error} />}
      {datos && datos.total === 0 && <Vacio titulo="Sin registros" descripcion="Ningún registro cumple los filtros elegidos." />}
      {datos && datos.total > 0 && (
        <>
          <div className={cn("border-2 bg-card shadow-md transition-opacity", consulta.isPlaceholderData && "opacity-60")}>
            <Table>
              <TableHeader>
                <TableRow className="bg-secondary hover:bg-secondary">
                  <Columna campo="id" titulo="ID" {...columnas} />
                  <Columna campo="temporada" titulo="Temporada" {...columnas} />
                  <Columna campo="etapa" titulo="Etapa" {...columnas} />
                  <Columna campo="dano" titulo="Daño" {...columnas} />
                  <Columna campo="magnitud" titulo="Magnitud" {...columnas} />
                  <Columna campo="exceso_verde" titulo="Exceso verde" {...columnas} className="text-right" />
                  <Columna campo="brillo" titulo="Brillo" {...columnas} className="text-right" />
                  <TableHead className="font-head">Subconjunto</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {datos.registros.map((registro) => (
                  <TableRow
                    key={registro.id}
                    tabIndex={0}
                    onClick={() => setSeleccionado(registro)}
                    onKeyDown={(evento) => evento.key === "Enter" && setSeleccionado(registro)}
                    className="cursor-pointer hover:bg-accent focus-visible:bg-accent focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-primary"
                  >
                    <TableCell className="font-mono text-xs">{registro.id}</TableCell>
                    <TableCell>{registro.temporada}</TableCell>
                    <TableCell>{etiquetas.etapa(registro.etapa)}</TableCell>
                    <TableCell>
                      <Badge variant={registro.dano === "DR" ? "secondary" : "outline"}>{etiquetas.dano(registro.dano)}</Badge>
                    </TableCell>
                    <TableCell>
                      <ChipMagnitud valor={registro.magnitud} />
                    </TableCell>
                    <TableCell className="text-right tabular-nums">{numero(registro.atributos.exceso_verde, 3)}</TableCell>
                    <TableCell className="text-right tabular-nums">{numero(registro.atributos.brillo, 1)}</TableCell>
                    <TableCell>{ETIQUETAS_SUBCONJUNTO[registro.subconjunto]}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
          <nav aria-label="Paginación de registros" className="flex flex-wrap items-center justify-between gap-3">
            <span className="text-sm text-muted-foreground">
              {entero(datos.total)} registros, página {datos.pagina} de {datos.paginas}
            </span>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" disabled={pagina <= 1} onClick={() => setPagina(pagina - 1)} aria-label="Página anterior">
                <ChevronLeft />
              </Button>
              {paginasVisibles(pagina, datos.paginas).map((numeroPagina) => (
                <Button
                  key={numeroPagina}
                  size="sm"
                  variant={numeroPagina === pagina ? "default" : "outline"}
                  aria-current={numeroPagina === pagina ? "page" : undefined}
                  onClick={() => setPagina(numeroPagina)}
                >
                  {numeroPagina}
                </Button>
              ))}
              <Button
                variant="outline"
                size="sm"
                disabled={pagina >= datos.paginas}
                onClick={() => setPagina(pagina + 1)}
                aria-label="Página siguiente"
              >
                <ChevronRight />
              </Button>
            </div>
          </nav>
        </>
      )}
      <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
        <MousePointerClick className="size-3.5" /> Pulse una fila para ver la fotografía y sus atributos.
      </p>
      <DetalleRegistro registro={seleccionado} onCerrar={() => setSeleccionado(null)} />
    </div>
  )
}
