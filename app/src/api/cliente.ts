import createClient from "openapi-fetch"

import type { components, operations, paths } from "@/api/esquema"

type Esquemas = components["schemas"]

export type Salud = Esquemas["Salud"]
export type Catalogos = Esquemas["Catalogos"]
export type Opcion = Esquemas["Opcion"]
export type Variable = Esquemas["Variable"]
export type Atributos = Esquemas["Atributos"]
export type Conteo = Esquemas["Conteo"]
export type ResumenDatos = Esquemas["ResumenDatos"]
export type Registro = Esquemas["Registro"]
export type Distribucion = Esquemas["Distribucion"]
export type Dispersion = Esquemas["Dispersion"]
export type ModeloInfo = Esquemas["ModeloInfo"]
export type ModeloDetalle = Esquemas["ModeloDetalle"]
export type Metricas = Esquemas["Metricas"]
export type PuntoPrediccion = Esquemas["PuntoPrediccion"]
export type Prediccion = Esquemas["Prediccion"]

export type FiltrosRegistros = NonNullable<operations["listar_registros"]["parameters"]["query"]>
export type ParametrosDistribucion = NonNullable<operations["obtener_distribucion"]["parameters"]["query"]>
export type VariableNumerica = operations["obtener_distribucion"]["parameters"]["path"]["variable"]
export type Alcance = Esquemas["Metricas"]["alcance"]
export type AgrupacionError = NonNullable<NonNullable<operations["listar_errores"]["parameters"]["query"]>["por"]>
export type Dano = Esquemas["Registro"]["dano"]

export const CODIGO_SIN_CONEXION = "sin_conexion"

export class ErrorApi extends Error {
  readonly estado: number
  readonly codigo: string

  constructor(estado: number, codigo: string, detalle: string) {
    super(detalle)
    this.name = "ErrorApi"
    this.estado = estado
    this.codigo = codigo
  }
}

const SIN_CONEXION = "No fue posible contactar la API. Verifique que el servidor este activo en el puerto 8000."

function esErrorContrato(valor: unknown): valor is Esquemas["Error"] {
  return typeof valor === "object" && valor !== null && "codigo" in valor && "detalle" in valor
}

function convertirError(estado: number, cuerpo: unknown) {
  if (esErrorContrato(cuerpo)) return new ErrorApi(estado, cuerpo.codigo, cuerpo.detalle)
  return new ErrorApi(estado, CODIGO_SIN_CONEXION, SIN_CONEXION)
}

export const cliente = createClient<paths>({ baseUrl: "" })

export async function datos<T>(peticion: Promise<{ data?: T; error?: unknown; response: Response }>): Promise<T> {
  let resultado
  try {
    resultado = await peticion
  } catch {
    throw new ErrorApi(0, CODIGO_SIN_CONEXION, SIN_CONEXION)
  }
  if (resultado.error !== undefined || !resultado.response.ok) {
    throw convertirError(resultado.response.status, resultado.error)
  }
  return resultado.data as T
}

export async function enviarPrediccion(imagen: File, dano: Dano | null, modelos: string[]) {
  const formulario = new FormData()
  formulario.append("imagen", imagen)
  formulario.append("dano", dano ?? "")
  for (const modelo of modelos) formulario.append("modelos", modelo)

  let respuesta: Response
  try {
    respuesta = await fetch("/api/predecir", { method: "POST", body: formulario })
  } catch {
    throw new ErrorApi(0, CODIGO_SIN_CONEXION, SIN_CONEXION)
  }
  const cuerpo: unknown = await respuesta.json().catch(() => null)
  if (!respuesta.ok) throw convertirError(respuesta.status, cuerpo)
  return cuerpo as Prediccion
}

export function urlImagen(registroId: string, lado = 512) {
  return `/api/datos/registros/${encodeURIComponent(registroId)}/imagen?lado=${lado}`
}
