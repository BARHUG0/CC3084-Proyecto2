import { useSearchParams } from "react-router"

export const TODOS = "todos"

export function useModeloSeleccionado(): [string, (valor: string) => void] {
  const [parametros, setParametros] = useSearchParams()
  const valor = parametros.get("modelo") ?? TODOS
  const cambiar = (nuevo: string) =>
    setParametros(
      (actuales) => {
        if (nuevo === TODOS) actuales.delete("modelo")
        else actuales.set("modelo", nuevo)
        return actuales
      },
      { replace: true },
    )
  return [valor, cambiar]
}

export function filtrarSeleccion<T>(elementos: T[], seleccion: string, clave: (elemento: T) => string) {
  return seleccion === TODOS ? elementos : elementos.filter((elemento) => clave(elemento) === seleccion)
}
