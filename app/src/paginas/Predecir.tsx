import { useEffect, useMemo, useRef, useState, type DragEvent } from "react"
import { ImageUp, Info, RotateCcw, Scale, X } from "lucide-react"

import type { Dano, ModeloInfo, Prediccion } from "@/api/cliente"
import { useModelos, usePredecir } from "@/api/consultas"
import { Bloque } from "@/components/Bloque"
import { Selector } from "@/components/Controles"
import { Encabezado } from "@/components/Encabezado"
import { AvisoError, Cargando, Vacio } from "@/components/Estados"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { Label } from "@/components/ui/label"
import { Spinner } from "@/components/ui/spinner"
import { Table, TableBody, TableCell, TableRow } from "@/components/ui/table"
import { useEtiquetas, useEtiquetasVariables } from "@/lib/catalogos"
import { colorMagnitud, etiquetaMagnitud } from "@/lib/colores"
import { useNotificarError } from "@/lib/errores"
import { numero } from "@/lib/formato"
import { cn } from "@/lib/utils"

const SIN_DIAGNOSTICO = "desconocido"
const TIPOS_ACEPTADOS = ["image/jpeg", "image/png"]
const TAMANO_MAXIMO = 15 * 1024 * 1024

function validarArchivo(archivo: File) {
  if (!TIPOS_ACEPTADOS.includes(archivo.type)) return "Solo se aceptan fotografías JPEG o PNG."
  if (archivo.size > TAMANO_MAXIMO) return "La fotografía supera el límite de 15 MB."
  return null
}

function ZonaImagen({ archivo, onArchivo }: { archivo: File | null; onArchivo: (archivo: File | null) => void }) {
  const entrada = useRef<HTMLInputElement>(null)
  const [arrastrando, setArrastrando] = useState(false)
  const [problema, setProblema] = useState<string | null>(null)
  const vista = useMemo(() => (archivo ? URL.createObjectURL(archivo) : null), [archivo])

  useEffect(() => {
    if (!vista) return
    return () => URL.revokeObjectURL(vista)
  }, [vista])

  const elegir = (lista: FileList | null) => {
    const elegido = lista?.[0]
    if (!elegido) return
    const error = validarArchivo(elegido)
    setProblema(error)
    if (!error) onArchivo(elegido)
  }

  const soltar = (evento: DragEvent) => {
    evento.preventDefault()
    setArrastrando(false)
    elegir(evento.dataTransfer.files)
  }

  return (
    <div className="flex flex-col gap-3">
      <input
        ref={entrada}
        type="file"
        accept={TIPOS_ACEPTADOS.join(",")}
        className="sr-only"
        aria-label="Fotografía del cultivo"
        onChange={(evento) => {
          elegir(evento.target.files)
          evento.target.value = ""
        }}
      />
      {vista && archivo ? (
        <div className="relative border-2 bg-card shadow-md">
          <img src={vista} alt="Fotografía elegida" className="aspect-[4/3] w-full object-contain" />
          <div className="flex items-center justify-between gap-2 border-t-2 p-2 text-sm">
            <span className="truncate font-bold">{archivo.name}</span>
            <Button size="sm" variant="outline" onClick={() => onArchivo(null)}>
              <X /> Quitar
            </Button>
          </div>
        </div>
      ) : (
        <button
          type="button"
          onClick={() => entrada.current?.click()}
          onDragOver={(evento) => {
            evento.preventDefault()
            setArrastrando(true)
          }}
          onDragLeave={() => setArrastrando(false)}
          onDrop={soltar}
          className={cn(
            "flex aspect-[4/3] w-full flex-col items-center justify-center gap-3 border-2 border-dashed bg-card p-6 text-center transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary",
            arrastrando && "border-solid bg-accent/40",
          )}
        >
          <span className="flex size-14 items-center justify-center border-2 bg-secondary shadow-sm">
            <ImageUp className="size-7" />
          </span>
          <span className="font-head">Arrastre una fotografía o pulse para elegirla</span>
          <span className="text-sm text-muted-foreground">JPEG o PNG, hasta 15 MB</span>
        </button>
      )}
      {problema && (
        <Alert status="error">
          <AlertTitle className="font-head">Archivo rechazado</AlertTitle>
          <AlertDescription>{problema}</AlertDescription>
        </Alert>
      )}
    </div>
  )
}

function SeleccionModelos({
  modelos,
  elegidos,
  onCambio,
}: {
  modelos: ModeloInfo[]
  elegidos: string[]
  onCambio: (ids: string[]) => void
}) {
  return (
    <fieldset className="flex flex-col gap-2">
      <legend className="mb-2 text-xs font-bold uppercase">Modelos</legend>
      {modelos.map((modelo) => {
        const id = `modelo-${modelo.id}`
        const marcado = elegidos.includes(modelo.id)
        return (
          <div key={modelo.id} className={cn("flex items-center gap-3 border-2 bg-card p-2", !modelo.disponible && "opacity-60")}>
            <Checkbox
              id={id}
              checked={marcado}
              disabled={!modelo.disponible}
              onCheckedChange={(valor) =>
                onCambio(valor ? [...elegidos, modelo.id] : elegidos.filter((elegido) => elegido !== modelo.id))
              }
            />
            <Label htmlFor={id} className="flex-1 cursor-pointer">
              {modelo.nombre}
            </Label>
            {!modelo.disponible && <Badge variant="outline">Sin artefacto</Badge>}
          </div>
        )
      })}
    </fieldset>
  )
}

function BarraMagnitud({ valor }: { valor: number }) {
  return (
    <div className="relative h-5 w-full border-2 bg-background" role="img" aria-label={`Magnitud ${numero(valor, 0)} de 100`}>
      <div className="h-full border-r-2" style={{ width: `${Math.max(0, Math.min(100, valor))}%`, backgroundColor: colorMagnitud(valor) }} />
    </div>
  )
}

function Resultado({ prediccion }: { prediccion: Prediccion }) {
  const etiquetas = useEtiquetas()
  const etiquetaVariable = useEtiquetasVariables()
  const atributos = Object.entries(prediccion.atributos).filter(([, valor]) => valor !== null && valor !== undefined)
  return (
    <div className="flex flex-col gap-5">
      <div className="flex flex-wrap items-center gap-2 text-sm">
        <span className="font-bold">Diagnóstico considerado:</span>
        <Badge variant={prediccion.dano_considerado ? "default" : "outline"}>
          {prediccion.dano_considerado ? etiquetas.dano(prediccion.dano_considerado) : "No indicado"}
        </Badge>
      </div>
      {prediccion.advertencias.map((advertencia) => (
        <Alert key={advertencia} status="warning">
          <Info />
          <AlertTitle className="font-head">Advertencia</AlertTitle>
          <AlertDescription>{advertencia}</AlertDescription>
        </Alert>
      ))}
      <div className="grid gap-4 sm:grid-cols-2">
        {prediccion.predicciones.map((p) => (
          <div key={p.modelo_id} className="flex flex-col gap-3 border-2 bg-card p-4 shadow-md">
            <div className="flex items-start justify-between gap-2">
              <span className="font-head">{p.nombre}</span>
              <span className="text-xs text-muted-foreground tabular-nums">{numero(p.tiempo_ms, 1)} ms</span>
            </div>
            <div className="flex items-baseline gap-2">
              <span className="font-head text-5xl tabular-nums">{p.magnitud_redondeada}</span>
              <span className="font-head text-xl">%</span>
              <span className="ml-auto flex items-center gap-1.5 border-2 bg-background px-2 py-0.5 text-xs font-bold">
                <span className="size-3 border-2" style={{ backgroundColor: colorMagnitud(p.magnitud_redondeada) }} />
                {etiquetaMagnitud(p.magnitud_redondeada)}
              </span>
            </div>
            <BarraMagnitud valor={p.magnitud} />
            <span className="text-xs text-muted-foreground">
              Estimación continua {numero(p.magnitud, 2)}, redondeada a la decena más cercana.
            </span>
            {p.regla_aplicada && (
              <span className="flex items-center gap-1.5 text-xs font-bold">
                <Scale className="size-4" /> Se aplicó la regla: diagnóstico distinto de sequía, magnitud 0.
              </span>
            )}
          </div>
        ))}
      </div>
      <details className="border-2 bg-card">
        <summary className="cursor-pointer p-3 font-head">Atributos calculados de la fotografía</summary>
        <Table className="border-t-2">
          <TableBody>
            {atributos.map(([clave, valor]) => (
              <TableRow key={clave}>
                <TableCell>{etiquetaVariable(clave)}</TableCell>
                <TableCell className="text-right font-bold tabular-nums">{numero(valor as number, 3)}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </details>
    </div>
  )
}

function Formulario({ modelos }: { modelos: ModeloInfo[] }) {
  const etiquetas = useEtiquetas()
  const prediccion = usePredecir()
  const disponibles = modelos.filter((modelo) => modelo.disponible)
  const [archivo, setArchivo] = useState<File | null>(null)
  const [dano, setDano] = useState<string>(SIN_DIAGNOSTICO)
  const [elegidos, setElegidos] = useState<string[]>(() => disponibles.map((modelo) => modelo.id))
  useNotificarError(prediccion.error)

  const opcionesDano = [
    { valor: SIN_DIAGNOSTICO, etiqueta: "No lo sé" },
    ...(etiquetas.catalogos?.danos ?? []).map((opcion) => ({ valor: opcion.codigo, etiqueta: opcion.nombre })),
  ]
  const listo = archivo !== null && elegidos.length > 0 && !prediccion.isPending

  const enviar = () => {
    if (!archivo) return
    prediccion.mutate({ imagen: archivo, dano: dano === SIN_DIAGNOSTICO ? null : (dano as Dano), modelos: elegidos })
  }

  const reiniciar = () => {
    setArchivo(null)
    prediccion.reset()
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[2fr_3fr]">
      <Bloque titulo="Fotografía y opciones">
        <div className="flex flex-col gap-5">
          <ZonaImagen
            archivo={archivo}
            onArchivo={(nuevo) => {
              setArchivo(nuevo)
              prediccion.reset()
            }}
          />
          <Selector etiqueta="Diagnóstico conocido" valor={dano} onCambio={setDano} opciones={opcionesDano} />
          {disponibles.length === 0 ? (
            <Alert status="warning">
              <AlertTitle className="font-head">No hay modelos entrenados</AlertTitle>
              <AlertDescription>Coloque al menos un artefacto entrenado en data/procesado/modelos/ para predecir.</AlertDescription>
            </Alert>
          ) : (
            <SeleccionModelos modelos={modelos} elegidos={elegidos} onCambio={setElegidos} />
          )}
          <div className="flex flex-wrap gap-3">
            <Button onClick={enviar} disabled={!listo} className="flex-1">
              {prediccion.isPending && <Spinner />}
              {prediccion.isPending ? "Estimando" : "Estimar magnitud"}
            </Button>
            <Button variant="outline" onClick={reiniciar} disabled={!archivo && !prediccion.data}>
              <RotateCcw /> Reiniciar
            </Button>
          </div>
          {archivo && elegidos.length === 0 && <span className="text-sm font-bold text-destructive">Elija al menos un modelo.</span>}
        </div>
      </Bloque>
      <Bloque titulo="Resultado" descripcion="Porcentaje estimado del cultivo dañado por sequía.">
        {prediccion.isPending && <Cargando alto="h-72" />}
        {prediccion.isError && <AvisoError error={prediccion.error} />}
        {prediccion.data && <Resultado prediccion={prediccion.data} />}
        {prediccion.isIdle && (
          <Vacio titulo="Sin estimación" descripcion="Elija una fotografía y pulse «Estimar magnitud» para ver el resultado de cada modelo." />
        )}
      </Bloque>
    </div>
  )
}

export default function Predecir() {
  const modelos = useModelos()
  return (
    <>
      <Encabezado
        etiqueta="Requisito d"
        titulo="Predecir"
        descripcion="Suba una fotografía del cultivo y obtenga la magnitud estimada del daño por sequía con cada modelo entrenado."
      />
      {modelos.isPending && <Cargando alto="h-96" />}
      {modelos.isError && <AvisoError error={modelos.error} />}
      {modelos.data && <Formulario modelos={modelos.data} />}
    </>
  )
}
