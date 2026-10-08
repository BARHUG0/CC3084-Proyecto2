export const PALETA = {
  principal: "#2E6F40",
  secundario: "#C9A227",
  terciario: "#8C3B2E",
  neutro: "#4A4A4A",
  claro: "#B8C9BC",
  fondo: "#F4EFE3",
  tinta: "#000000",
} as const

export const SECUENCIA_COLORES = [
  "#2E6F40",
  "#C9A227",
  "#8C3B2E",
  "#3C6E93",
  "#7A5C99",
  "#B87333",
  "#5B8C5A",
  "#A6A6A6",
] as const

const PARADAS_MAGNITUD = [
  { valor: 0, color: [79, 138, 85] },
  { valor: 50, color: [201, 162, 39] },
  { valor: 100, color: [140, 59, 46] },
] as const

export function colorSerie(indice: number) {
  return SECUENCIA_COLORES[indice % SECUENCIA_COLORES.length]
}

export function colorMagnitud(magnitud: number) {
  const valor = Math.min(100, Math.max(0, magnitud))
  const tramo = valor <= 50 ? 0 : 1
  const inicio = PARADAS_MAGNITUD[tramo]
  const fin = PARADAS_MAGNITUD[tramo + 1]
  const t = (valor - inicio.valor) / (fin.valor - inicio.valor)
  const [r, g, b] = inicio.color.map((canal, i) => Math.round(canal + t * (fin.color[i] - canal)))
  return `rgb(${r}, ${g}, ${b})`
}

export function etiquetaMagnitud(magnitud: number) {
  if (magnitud < 20) return "Leve"
  if (magnitud < 50) return "Moderado"
  if (magnitud < 80) return "Severo"
  return "Muy severo"
}
