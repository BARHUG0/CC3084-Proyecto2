import { BarChart3, Brain, Camera, Home, Table2, type LucideIcon } from "lucide-react"

export type Seccion = {
  ruta: string
  titulo: string
  descripcion: string
  icono: LucideIcon
}

export const SECCIONES: Seccion[] = [
  { ruta: "/", titulo: "Inicio", descripcion: "Estado del sistema y resumen del conjunto.", icono: Home },
  {
    ruta: "/explorar",
    titulo: "Explorar datos",
    descripcion: "Distribuciones, relaciones y registros del conjunto de modelado.",
    icono: Table2,
  },
  {
    ruta: "/modelos",
    titulo: "Modelos",
    descripcion: "Familia, entradas, hiperparámetros y ajuste de cada modelo.",
    icono: Brain,
  },
  {
    ruta: "/rendimiento",
    titulo: "Rendimiento",
    descripcion: "Errores, valor real contra predicho y tiempos sobre el conjunto de prueba.",
    icono: BarChart3,
  },
  {
    ruta: "/predecir",
    titulo: "Predecir",
    descripcion: "Estimar la magnitud del daño por sequía de una fotografía.",
    icono: Camera,
  },
]
