import { CheckCircle2, XCircle } from "lucide-react"

import type { ModeloDetalle, ModeloInfo } from "@/api/cliente"
import { useModelos, useModelosDetalle } from "@/api/consultas"
import { Bloque } from "@/components/Bloque"
import { Encabezado } from "@/components/Encabezado"
import { AvisoError, Cargando, Contenido, Vacio } from "@/components/Estados"
import { GraficoBarras } from "@/components/graficos/GraficoBarras"
import { GraficoLineas } from "@/components/graficos/GraficoLineas"
import { SelectorModelos } from "@/components/SelectorModelos"
import { Badge } from "@/components/ui/badge"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { FAMILIAS, useEtiquetasVariables } from "@/lib/catalogos"
import { PALETA } from "@/lib/colores"
import { numero } from "@/lib/formato"
import { filtrarSeleccion, useModeloSeleccionado } from "@/lib/seleccion"

type Parametros = ModeloInfo["hiperparametros"]

function valorParametro(valor: Parametros[string]) {
  if (valor === null) return "ninguno"
  if (typeof valor === "boolean") return valor ? "sí" : "no"
  if (typeof valor === "number") return Number.isInteger(valor) ? String(valor) : numero(valor, 4)
  return valor
}

function textoParametros(parametros: Parametros) {
  return Object.entries(parametros)
    .map(([clave, valor]) => `${clave} = ${valorParametro(valor)}`)
    .join(", ")
}

function Estado({ activo, texto }: { activo: boolean; texto: string }) {
  const Icono = activo ? CheckCircle2 : XCircle
  return (
    <span className="flex items-center gap-1.5 text-sm">
      <Icono className={activo ? "size-4 text-primary" : "size-4 text-destructive"} />
      {texto}
    </span>
  )
}

function FichaModelo({ modelo }: { modelo: ModeloInfo }) {
  const etiquetaVariable = useEtiquetasVariables()
  const parametros = Object.entries(modelo.hiperparametros)
  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center gap-2">
        <Badge>{FAMILIAS[modelo.familia] ?? modelo.familia}</Badge>
        <span className="font-mono text-xs text-muted-foreground">{modelo.id}</span>
      </div>
      <p className="text-sm">{modelo.descripcion}</p>
      <div className="flex flex-wrap gap-4">
        <Estado activo={modelo.disponible} texto={modelo.disponible ? "Artefacto entrenado" : "Sin artefacto"} />
        <Estado activo={modelo.tiene_resultados} texto={modelo.tiene_resultados ? "Con resultados de prueba" : "Sin resultados"} />
      </div>
      <div>
        <h3 className="mb-2 font-head text-sm uppercase">Entradas</h3>
        <div className="flex flex-wrap gap-1">
          {modelo.entradas.length === 0 && <span className="text-sm text-muted-foreground">No usa variables de entrada.</span>}
          {modelo.entradas.map((entrada) => (
            <Badge key={entrada} variant="outline">
              {etiquetaVariable(entrada)}
            </Badge>
          ))}
        </div>
      </div>
      <div>
        <h3 className="mb-2 font-head text-sm uppercase">Hiperparámetros elegidos</h3>
        {parametros.length === 0 ? (
          <span className="text-sm text-muted-foreground">Sin hiperparámetros.</span>
        ) : (
          <Table className="border-2">
            <TableBody>
              {parametros.map(([clave, valor]) => (
                <TableRow key={clave}>
                  <TableCell className="font-mono text-xs">{clave}</TableCell>
                  <TableCell className="text-right font-bold">{valorParametro(valor)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>
    </div>
  )
}

function HistorialAjuste({ detalle }: { detalle: ModeloDetalle }) {
  if (detalle.historial_ajuste.length === 0) {
    return <Vacio titulo="Sin búsqueda de hiperparámetros" descripcion="Este modelo no registró combinaciones evaluadas." />
  }
  const pasos = [...detalle.historial_ajuste].sort((a, b) => a.rmse_validacion - b.rmse_validacion)
  const filas = pasos.map((paso, indice) => ({
    combinacion: `#${indice + 1}`,
    rmse: paso.rmse_validacion,
    mae: paso.mae_validacion ?? null,
  }))
  const tieneMae = filas.some((fila) => fila.mae !== null)
  return (
    <div className="flex flex-col gap-4">
      <GraficoBarras
        datos={filas}
        categoria="combinacion"
        series={[
          { clave: "rmse", nombre: "RMSE de validación", color: PALETA.principal },
          ...(tieneMae ? [{ clave: "mae", nombre: "MAE de validación", color: PALETA.secundario }] : []),
        ]}
        colorBarra={(fila, serie) =>
          serie.clave === "rmse" && fila.combinacion === "#1" ? PALETA.terciario : serie.color
        }
        zoom
        formato={(v) => numero(v, 2)}
        etiquetaX="Combinación, ordenada de mejor a peor"
        etiquetaY="Error"
      />
      <p className="text-xs text-muted-foreground">La barra terracota marca la combinación elegida.</p>
      <div tabIndex={0} role="region" aria-label="Combinaciones evaluadas" className="max-h-72 overflow-auto border-2">
        <Table>
          <TableHeader className="sticky top-0">
            <TableRow className="bg-secondary hover:bg-secondary">
              <TableHead className="font-head">#</TableHead>
              <TableHead className="font-head">Parámetros</TableHead>
              <TableHead className="text-right font-head">RMSE</TableHead>
              {tieneMae && <TableHead className="text-right font-head">MAE</TableHead>}
            </TableRow>
          </TableHeader>
          <TableBody>
            {pasos.map((paso, indice) => (
              <TableRow key={indice} className={indice === 0 ? "bg-accent/40 font-bold" : undefined}>
                <TableCell>{indice + 1}</TableCell>
                <TableCell className="font-mono text-xs whitespace-normal">{textoParametros(paso.parametros)}</TableCell>
                <TableCell className="text-right">{numero(paso.rmse_validacion, 3)}</TableCell>
                {tieneMae && <TableCell className="text-right">{numero(paso.mae_validacion, 3)}</TableCell>}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  )
}

function CurvaEntrenamiento({ detalle }: { detalle: ModeloDetalle }) {
  if (detalle.curva_entrenamiento.length === 0) {
    return <Vacio titulo="Sin curva de entrenamiento" descripcion="Solo las redes convolucionales registran pérdida por época." />
  }
  const filas = detalle.curva_entrenamiento.map((epoca) => ({
    epoca: epoca.epoca,
    entrenamiento: epoca.perdida_entrenamiento,
    validacion: epoca.perdida_validacion ?? null,
  }))
  return (
    <GraficoLineas
      datos={filas}
      categoria="epoca"
      series={[
        { clave: "entrenamiento", nombre: "Entrenamiento", color: PALETA.principal },
        { clave: "validacion", nombre: "Validación", color: PALETA.terciario },
      ]}
      etiquetaX="Época"
      etiquetaY="Pérdida"
    />
  )
}

function Importancias({ detalle }: { detalle: ModeloDetalle }) {
  const etiquetaVariable = useEtiquetasVariables()
  if (detalle.importancias.length === 0) {
    return <Vacio titulo="Sin importancias" descripcion="Solo los modelos tabulares basados en árboles reportan importancia de variables." />
  }
  const filas = [...detalle.importancias]
    .sort((a, b) => b.importancia - a.importancia)
    .map((item) => ({ variable: etiquetaVariable(item.variable), importancia: item.importancia }))
  return (
    <GraficoBarras
      datos={filas}
      categoria="variable"
      series={[{ clave: "importancia", nombre: "Importancia", color: PALETA.principal }]}
      horizontal
      alto={Math.max(240, filas.length * 30)}
      anchoCategoria={170}
      formato={(v) => numero(v, 3)}
      etiquetaX="Importancia relativa"
    />
  )
}

function DetalleModelo({ detalle }: { detalle: ModeloDetalle }) {
  return (
    <Tabs defaultValue="ajuste">
      <TabsList>
        <TabsTrigger value="ajuste">Ajuste</TabsTrigger>
        <TabsTrigger value="curva">Curva</TabsTrigger>
        <TabsTrigger value="importancias">Importancias</TabsTrigger>
      </TabsList>
      <TabsContent value="ajuste" className="mt-4">
        <HistorialAjuste detalle={detalle} />
      </TabsContent>
      <TabsContent value="curva" className="mt-4">
        <CurvaEntrenamiento detalle={detalle} />
      </TabsContent>
      <TabsContent value="importancias" className="mt-4">
        <Importancias detalle={detalle} />
      </TabsContent>
    </Tabs>
  )
}

function ListaModelos({ modelos }: { modelos: ModeloInfo[] }) {
  const [seleccion] = useModeloSeleccionado()
  const filtrados = filtrarSeleccion(modelos, seleccion, (modelo) => modelo.id)
  const visibles = filtrados.length > 0 ? filtrados : modelos
  const detalles = useModelosDetalle(visibles.map((modelo) => modelo.id))
  return (
    <div className="grid gap-6">
      {visibles.map((modelo, indice) => {
        const consulta = detalles[indice]
        return (
          <Bloque key={modelo.id} titulo={modelo.nombre}>
            <div className="grid gap-6 lg:grid-cols-[1fr_2fr]">
              <FichaModelo modelo={modelo} />
              <div className="min-w-0">
                {consulta.isPending && <Cargando alto="h-72" />}
                {consulta.isError && <AvisoError error={consulta.error} />}
                {consulta.data && <DetalleModelo detalle={consulta.data} />}
              </div>
            </div>
          </Bloque>
        )
      })}
    </div>
  )
}

export default function Modelos() {
  const modelos = useModelos()
  return (
    <>
      <Encabezado
        etiqueta="Requisito b"
        titulo="Modelos"
        descripcion="Algoritmos entrenados, variables que usan, hiperparámetros elegidos y el proceso de ajuste que llevó a ellos."
      >
        {modelos.data && modelos.data.length > 0 && <SelectorModelos modelos={modelos.data} />}
      </Encabezado>
      <Contenido
        consulta={modelos}
        alto="h-96"
        esVacio={(datos) => datos.length === 0}
        mensajeVacio="No hay modelos registrados en la API."
      >
        {(datos) => <ListaModelos modelos={datos} />}
      </Contenido>
    </>
  )
}
