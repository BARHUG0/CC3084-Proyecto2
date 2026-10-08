import { lazy, Suspense } from "react"
import { Route, Routes } from "react-router"

import { Disposicion } from "@/components/Disposicion"
import { Cargando, Vacio } from "@/components/Estados"
import Inicio from "@/paginas/Inicio"

const Explorar = lazy(() => import("@/paginas/Explorar"))
const Modelos = lazy(() => import("@/paginas/Modelos"))
const Rendimiento = lazy(() => import("@/paginas/Rendimiento"))
const Predecir = lazy(() => import("@/paginas/Predecir"))

export default function App() {
  return (
    <Routes>
      <Route element={<Disposicion />}>
        <Route index element={<Inicio />} />
        <Route
          path="explorar"
          element={
            <Suspense fallback={<Cargando alto="h-96" />}>
              <Explorar />
            </Suspense>
          }
        />
        <Route
          path="modelos"
          element={
            <Suspense fallback={<Cargando alto="h-96" />}>
              <Modelos />
            </Suspense>
          }
        />
        <Route
          path="rendimiento"
          element={
            <Suspense fallback={<Cargando alto="h-96" />}>
              <Rendimiento />
            </Suspense>
          }
        />
        <Route
          path="predecir"
          element={
            <Suspense fallback={<Cargando alto="h-96" />}>
              <Predecir />
            </Suspense>
          }
        />
        <Route path="*" element={<Vacio titulo="Página no encontrada" descripcion="La ruta solicitada no existe." />} />
      </Route>
    </Routes>
  )
}
