import { useMemo } from "react"

import type { Catalogos } from "@/api/cliente"
import { useCatalogos, useVariables } from "@/api/consultas"

export const VARIABLES_NUMERICAS = [
  "magnitud",
  "exceso_verde",
  "saturacion",
  "brillo",
  "contraste",
  "media_r",
  "media_g",
  "media_b",
  "nitidez",
  "megapixeles",
  "aspecto",
  "prop_sobreexpuesta",
  "prop_subexpuesta",
] as const

export const ETIQUETAS_SUBCONJUNTO: Record<string, string> = { entrenamiento: "Entrenamiento", prueba: "Prueba" }

function mapa(opciones: Catalogos["danos"] | undefined) {
  return Object.fromEntries((opciones ?? []).map((opcion) => [opcion.codigo, opcion.nombre]))
}

export const FAMILIAS: Record<string, string> = { referencia: "Referencia", tabular: "Tabular", cnn: "Red convolucional" }

export function useEtiquetasVariables() {
  const { data } = useVariables()
  return useMemo(() => {
    const etiquetas = Object.fromEntries((data ?? []).map((variable) => [variable.nombre, variable.etiqueta]))
    return (nombre: string) => etiquetas[nombre] ?? nombre
  }, [data])
}

export function useEtiquetas() {
  const { data } = useCatalogos()
  return useMemo(() => {
    const danos = mapa(data?.danos)
    const etapas = mapa(data?.etapas)
    const capturas = mapa(data?.tipos_captura)
    return {
      catalogos: data,
      dano: (codigo: string | null | undefined) => (codigo ? (danos[codigo] ?? codigo) : "Sin dato"),
      etapa: (codigo: string | null | undefined) => (codigo ? (etapas[codigo] ?? codigo) : "Sin dato"),
      captura: (codigo: string | null | undefined) => (codigo ? (capturas[codigo] ?? codigo) : "Sin dato"),
    }
  }, [data])
}
