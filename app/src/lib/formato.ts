const LOCALE = "es-GT"

export function numero(valor: number | null | undefined, decimales = 2) {
  if (valor === null || valor === undefined || Number.isNaN(valor)) return "n/d"
  return valor.toLocaleString(LOCALE, { minimumFractionDigits: decimales, maximumFractionDigits: decimales })
}

export function entero(valor: number) {
  return valor.toLocaleString(LOCALE)
}

export function plural(cantidad: number, singular: string, varios: string) {
  return `${entero(cantidad)} ${cantidad === 1 ? singular : varios}`
}

export function porcentaje(parte: number, total: number) {
  if (total === 0) return "0 %"
  return `${numero((100 * parte) / total, 1)} %`
}

export function duracion(segundos: number) {
  if (segundos < 1) return `${numero(segundos * 1000, 1)} ms`
  if (segundos < 120) return `${numero(segundos, 2)} s`
  return `${numero(segundos / 60, 1)} min`
}
