import { useEffect } from "react"
import { toast } from "sonner"

import { CODIGO_SIN_CONEXION, ErrorApi } from "@/api/cliente"

const INSTRUCCIONES: Record<string, { titulo: string; instruccion: string }> = {
  [CODIGO_SIN_CONEXION]: {
    titulo: "La API no responde",
    instruccion: "Levante el backend con «uvicorn src.api:app --port 8000» o con «python -m src.demo».",
  },
  datos_no_disponibles: {
    titulo: "No hay conjunto de modelado",
    instruccion: "Ejecute «python -m src.conjunto» o use el backend de demostración con «python -m src.demo».",
  },
  sin_resultados: {
    titulo: "Modelo sin resultados",
    instruccion: "Entrene el modelo y guarde sus resultados en data/procesado/resultados/.",
  },
  sin_modelos_disponibles: {
    titulo: "No hay modelos entrenados",
    instruccion: "Coloque al menos un artefacto entrenado en data/procesado/modelos/.",
  },
  modelo_no_disponible: {
    titulo: "Modelo sin artefacto",
    instruccion: "Quite ese modelo de la selección o entrénelo primero.",
  },
  imagen_no_disponible: {
    titulo: "Fotografía no descargada",
    instruccion: "Descargue las imágenes con «python -m src.descarga imagenes».",
  },
  imagen_invalida: {
    titulo: "Imagen no válida",
    instruccion: "Elija otra fotografía JPEG o PNG.",
  },
  formato_no_soportado: {
    titulo: "Formato no soportado",
    instruccion: "Solo se aceptan fotografías JPEG o PNG.",
  },
  imagen_demasiado_grande: {
    titulo: "Imagen demasiado grande",
    instruccion: "Reduzca la fotografía a menos de 15 MB.",
  },
}

export const CODIGOS_ADVERTENCIA = new Set(["datos_no_disponibles", "sin_resultados", "sin_modelos_disponibles"])

export function describirError(error: unknown) {
  if (error instanceof ErrorApi) {
    const conocido = INSTRUCCIONES[error.codigo]
    return {
      titulo: conocido?.titulo ?? "Error de la API",
      detalle: error.message,
      instruccion: conocido?.instruccion,
      codigo: error.codigo,
    }
  }
  return { titulo: "Error inesperado", detalle: String(error), instruccion: undefined, codigo: "desconocido" }
}

export function useNotificarError(error: unknown) {
  useEffect(() => {
    if (!error) return
    const { titulo, detalle, codigo } = describirError(error)
    if (CODIGOS_ADVERTENCIA.has(codigo)) return
    toast.error(titulo, { description: detalle, id: `${codigo}:${detalle}` })
  }, [error])
}
