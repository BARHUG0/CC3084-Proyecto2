import type { ReactNode } from "react"
import { AlertTriangle, Inbox, PlugZap } from "lucide-react"

import { CODIGO_SIN_CONEXION } from "@/api/cliente"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Empty, EmptyDescription, EmptyHeader, EmptyMedia, EmptyTitle } from "@/components/ui/empty"
import { Skeleton } from "@/components/ui/skeleton"
import { CODIGOS_ADVERTENCIA, describirError } from "@/lib/errores"
import { cn } from "@/lib/utils"

export function AvisoError({ error, className }: { error: unknown; className?: string }) {
  const { titulo, detalle, instruccion, codigo } = describirError(error)
  const Icono = codigo === CODIGO_SIN_CONEXION ? PlugZap : AlertTriangle
  return (
    <Alert status={CODIGOS_ADVERTENCIA.has(codigo) ? "warning" : "error"} className={className}>
      <Icono />
      <AlertTitle className="font-head">{titulo}</AlertTitle>
      <AlertDescription>
        <p>{detalle}</p>
        {instruccion && <p className="font-semibold">{instruccion}</p>}
      </AlertDescription>
    </Alert>
  )
}

export function Cargando({ alto = "h-64", className }: { alto?: string; className?: string }) {
  return <Skeleton className={cn("w-full", alto, className)} />
}

type ConsultaBasica<T> = { data: T | undefined; error: unknown; isPending: boolean; isError?: boolean }

export function Contenido<T>({
  consulta,
  alto,
  esVacio,
  mensajeVacio = "No hay datos para mostrar.",
  children,
}: {
  consulta: ConsultaBasica<T>
  alto?: string
  esVacio?: (datos: T) => boolean
  mensajeVacio?: string
  children: (datos: T) => ReactNode
}) {
  if (consulta.isPending) return <Cargando alto={alto} />
  if (consulta.data === undefined) return <AvisoError error={consulta.error} />
  if (esVacio?.(consulta.data)) return <Vacio titulo="Sin datos" descripcion={mensajeVacio} />
  return (
    <>
      {consulta.isError && (
        <Alert status="warning" className="mb-4">
          <AlertTriangle />
          <AlertTitle className="font-head">Datos desactualizados</AlertTitle>
          <AlertDescription>Se muestra la última lectura conocida; la API no respondió a la actualización.</AlertDescription>
        </Alert>
      )}
      {children(consulta.data)}
    </>
  )
}

export function Vacio({ titulo, descripcion, children }: { titulo: string; descripcion?: string; children?: ReactNode }) {
  return (
    <Empty className="min-h-48">
      <EmptyHeader>
        <EmptyMedia variant="icon">
          <Inbox />
        </EmptyMedia>
        <EmptyTitle className="font-head">{titulo}</EmptyTitle>
        {descripcion && <EmptyDescription>{descripcion}</EmptyDescription>}
      </EmptyHeader>
      {children}
    </Empty>
  )
}
