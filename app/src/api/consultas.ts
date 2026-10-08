import { keepPreviousData, QueryClient, useMutation, useQueries, useQuery } from "@tanstack/react-query"

import {
  cliente,
  datos,
  enviarPrediccion,
  ErrorApi,
  type AgrupacionError,
  type Alcance,
  type Dano,
  type FiltrosRegistros,
  type ParametrosDistribucion,
  type VariableNumerica,
} from "@/api/cliente"

const CODIGOS_SIN_REINTENTO = new Set(["datos_no_disponibles", "sin_resultados", "modelo_no_encontrado"])

function reintentar(intentos: number, error: Error) {
  if (error instanceof ErrorApi && (CODIGOS_SIN_REINTENTO.has(error.codigo) || (error.estado >= 400 && error.estado < 500))) {
    return false
  }
  return intentos < 2
}

export function crearClienteConsultas() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: reintentar, staleTime: 30_000, refetchOnWindowFocus: false },
    },
  })
}

export function useSalud() {
  return useQuery({
    queryKey: ["salud"],
    queryFn: () => datos(cliente.GET("/api/salud")),
    refetchInterval: 15_000,
  })
}

export function useCatalogos() {
  return useQuery({
    queryKey: ["catalogos"],
    queryFn: () => datos(cliente.GET("/api/catalogos")),
    staleTime: Infinity,
  })
}

export function useVariables() {
  return useQuery({
    queryKey: ["variables"],
    queryFn: () => datos(cliente.GET("/api/datos/variables")),
  })
}

export function useResumen() {
  return useQuery({
    queryKey: ["resumen"],
    queryFn: () => datos(cliente.GET("/api/datos/resumen")),
  })
}

export function useRegistros(filtros: FiltrosRegistros) {
  return useQuery({
    queryKey: ["registros", filtros],
    queryFn: () => datos(cliente.GET("/api/datos/registros", { params: { query: filtros } })),
    placeholderData: keepPreviousData,
  })
}

export function useDistribucion(variable: VariableNumerica, parametros: ParametrosDistribucion) {
  return useQuery({
    queryKey: ["distribucion", variable, parametros],
    queryFn: () =>
      datos(cliente.GET("/api/datos/distribucion/{variable}", { params: { path: { variable }, query: parametros } })),
    placeholderData: keepPreviousData,
  })
}

export function useDispersion(x: VariableNumerica, soloDr: boolean, muestra = 1500) {
  return useQuery({
    queryKey: ["dispersion", x, soloDr, muestra],
    queryFn: () => datos(cliente.GET("/api/datos/dispersion", { params: { query: { x, solo_dr: soloDr, muestra } } })),
    placeholderData: keepPreviousData,
  })
}

export function useCorrelaciones(soloDr: boolean) {
  return useQuery({
    queryKey: ["correlaciones", soloDr],
    queryFn: () => datos(cliente.GET("/api/datos/correlaciones", { params: { query: { solo_dr: soloDr } } })),
  })
}

export function useModelos() {
  return useQuery({
    queryKey: ["modelos"],
    queryFn: () => datos(cliente.GET("/api/modelos")),
  })
}

export function useModelosDetalle(ids: string[]) {
  return useQueries({
    queries: ids.map((modeloId) => ({
      queryKey: ["modelo", modeloId],
      queryFn: () => datos(cliente.GET("/api/modelos/{modelo_id}", { params: { path: { modelo_id: modeloId } } })),
    })),
  })
}

export function useMetricas(alcance: Alcance) {
  return useQuery({
    queryKey: ["metricas", alcance],
    queryFn: () => datos(cliente.GET("/api/metricas", { params: { query: { alcance } } })),
  })
}

export function usePredicciones(ids: string[], alcance: Alcance, limite = 2000) {
  return useQueries({
    queries: ids.map((modeloId) => ({
      queryKey: ["predicciones", modeloId, alcance, limite],
      queryFn: () =>
        datos(
          cliente.GET("/api/metricas/{modelo_id}/predicciones", {
            params: { path: { modelo_id: modeloId }, query: { alcance, limite } },
          }),
        ),
    })),
  })
}

export function useErrores(ids: string[], por: AgrupacionError, alcance: Alcance) {
  return useQueries({
    queries: ids.map((modeloId) => ({
      queryKey: ["errores", modeloId, por, alcance],
      queryFn: () =>
        datos(
          cliente.GET("/api/metricas/{modelo_id}/errores", {
            params: { path: { modelo_id: modeloId }, query: { por, alcance } },
          }),
        ),
    })),
  })
}

export function usePredecir() {
  return useMutation({
    mutationFn: ({ imagen, dano, modelos }: { imagen: File; dano: Dano | null; modelos: string[] }) =>
      enviarPrediccion(imagen, dano, modelos),
  })
}
