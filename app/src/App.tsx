import { Route, Routes } from "react-router"

import { Disposicion } from "@/components/Disposicion"
import { Vacio } from "@/components/Estados"
import Explorar from "@/paginas/Explorar"
import Inicio from "@/paginas/Inicio"
import Modelos from "@/paginas/Modelos"
import Predecir from "@/paginas/Predecir"
import Rendimiento from "@/paginas/Rendimiento"

export default function App() {
  return (
    <Routes>
      <Route element={<Disposicion />}>
        <Route index element={<Inicio />} />
        <Route path="explorar" element={<Explorar />} />
        <Route path="modelos" element={<Modelos />} />
        <Route path="rendimiento" element={<Rendimiento />} />
        <Route path="predecir" element={<Predecir />} />
        <Route path="*" element={<Vacio titulo="Página no encontrada" descripcion="La ruta solicitada no existe." />} />
      </Route>
    </Routes>
  )
}
