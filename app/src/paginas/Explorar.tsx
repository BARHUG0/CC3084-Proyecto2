import { useState } from "react"

import type { Conteo, Opcion, ResumenDatos, VariableNumerica } from "@/api/cliente"
import { useCorrelaciones, useDispersion, useDistribucion, useModelos, useResumen, useVariables } from "@/api/consultas"
import { Bloque } from "@/components/Bloque"
import { Alternador, Interruptor, Selector } from "@/components/Controles"
import { Encabezado } from "@/components/Encabezado"
import { Contenido } from "@/components/Estados"
import { GraficoBarras, type FilaGrafico } from "@/components/graficos/GraficoBarras"
import { GraficoDispersion } from "@/components/graficos/GraficoDispersion"
import { TablaRegistros } from "@/components/TablaRegistros"
import { Badge } from "@/components/ui/badge"
import { Label } from "@/components/ui/label"
import { Slider } from "@/components/ui/slider"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { VARIABLES_NUMERICAS, useEtiquetas, useEtiquetasVariables } from "@/lib/catalogos"
import { colorMagnitud, colorSerie, PALETA } from "@/lib/colores"
import { entero, numero } from "@/lib/formato"

type Agrupacion = "ninguno" | "dano" | "temporada" | "etapa"

const AGRUPACIONES: { valor: Agrupacion; etiqueta: string }[] = [
  { valor: "ninguno", etiqueta: "Sin agrupar" },
  { valor: "dano", etiqueta: "Por daño" },
  { valor: "temporada", etiqueta: "Por temporada" },
  { valor: "etapa", etiqueta: "Por etapa" },
]

function colorCategoria(lista: Opcion[] | undefined, codigo: string) {
  const indice = (lista ?? []).findIndex((opcion) => opcion.codigo === codigo)
  return colorSerie(Math.max(0, indice))
}

function filasConteo(conteos: Conteo[]): FilaGrafico[] {
  return conteos.map((c) => ({ clave: c.clave, etiqueta: c.etiqueta, conteo: c.conteo }))
}

function formatoBorde(valor: number) {
  const absoluto = Math.abs(valor)
  return numero(valor, absoluto >= 100 ? 0 : absoluto >= 1 ? 1 : 3)
}

function ResumenConteos({ resumen }: { resumen: ResumenDatos }) {
  const { catalogos } = useEtiquetas()
  const [alcance, setAlcance] = useState<"global" | "dr">("dr")
  const serie = [{ clave: "conteo", nombre: "Registros", color: PALETA.principal }]
  const pestanas = [
    { valor: "temporada", titulo: "Temporada", datos: resumen.por_temporada, lista: catalogos?.temporadas },
    { valor: "dano", titulo: "Daño", datos: resumen.por_dano, lista: catalogos?.danos },
    { valor: "etapa", titulo: "Etapa", datos: resumen.por_etapa, lista: catalogos?.etapas },
  ]
  const magnitud = alcance === "dr" ? resumen.magnitud_dr : resumen.magnitud_global
  return (
    <Tabs defaultValue="magnitud">
      <TabsList>
        <TabsTrigger value="magnitud">Magnitud</TabsTrigger>
        {pestanas.map((p) => (
          <TabsTrigger key={p.valor} value={p.valor}>
            {p.titulo}
          </TabsTrigger>
        ))}
      </TabsList>
      <TabsContent value="magnitud" className="mt-4 flex flex-col gap-3">
        <Alternador
          etiqueta="Alcance de la magnitud"
          valor={alcance}
          onCambio={setAlcance}
          opciones={[
            { valor: "dr", etiqueta: "Solo sequía" },
            { valor: "global", etiqueta: "Todos los registros" },
          ]}
        />
        <GraficoBarras
          datos={filasConteo(magnitud)}
          categoria="etiqueta"
          series={serie}
          colorBarra={(fila) => colorMagnitud(Number(fila.clave))}
          formato={(v) => entero(v)}
          etiquetaX="Magnitud del daño"
          etiquetaY="Registros"
        />
      </TabsContent>
      {pestanas.map((p) => (
        <TabsContent key={p.valor} value={p.valor} className="mt-4">
          <GraficoBarras
            datos={filasConteo(p.datos)}
            categoria="etiqueta"
            series={serie}
            colorBarra={(fila) => colorCategoria(p.lista, String(fila.clave))}
            formato={(v) => entero(v)}
            etiquetaY="Registros"
          />
        </TabsContent>
      ))}
    </Tabs>
  )
}

function TablaVariables() {
  const variables = useVariables()
  const modelos = useModelos()
  const nombreModelo = (id: string) => modelos.data?.find((m) => m.id === id)?.nombre ?? id
  return (
    <Contenido consulta={variables} esVacio={(d) => d.length === 0}>
      {(datos) => (
        <div className="max-h-[28rem] overflow-auto border-2">
          <Table>
            <TableHeader className="sticky top-0 z-10">
              <TableRow className="bg-secondary hover:bg-secondary">
                <TableHead className="font-head">Variable</TableHead>
                <TableHead className="font-head">Rol</TableHead>
                <TableHead className="font-head">Modelos que la usan</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {datos.map((variable) => (
                <TableRow key={variable.nombre}>
                  <TableCell className="max-w-sm whitespace-normal">
                    <span className="block font-bold">
                      {variable.etiqueta} <span className="font-mono text-xs font-normal text-muted-foreground">{variable.nombre}</span>
                    </span>
                    <span className="block text-xs text-muted-foreground">{variable.descripcion}</span>
                  </TableCell>
                  <TableCell>
                    <Badge variant={variable.rol === "objetivo" ? "default" : variable.rol === "atributo" ? "secondary" : "outline"}>
                      {variable.rol}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div className="flex flex-wrap gap-1">
                      {variable.usada_en_modelos.length === 0 && <span className="text-xs text-muted-foreground">Ninguno</span>}
                      {variable.usada_en_modelos.map((id) => (
                        <Badge key={id} variant="outline">
                          {nombreModelo(id)}
                        </Badge>
                      ))}
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </Contenido>
  )
}

function Histograma() {
  const etiquetaVariable = useEtiquetasVariables()
  const { catalogos } = useEtiquetas()
  const [variable, setVariable] = useState<VariableNumerica>("exceso_verde")
  const [por, setPor] = useState<Agrupacion>("dano")
  const [bins, setBins] = useState(20)
  const [soloDr, setSoloDr] = useState(false)
  const consulta = useDistribucion(variable, { por, bins, solo_dr: soloDr })

  const listas: Record<Agrupacion, Opcion[] | undefined> = {
    ninguno: undefined,
    dano: catalogos?.danos,
    temporada: catalogos?.temporadas,
    etapa: catalogos?.etapas,
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-end gap-4">
        <Selector
          etiqueta="Variable"
          valor={variable}
          onCambio={setVariable}
          opciones={VARIABLES_NUMERICAS.map((v) => ({ valor: v, etiqueta: etiquetaVariable(v) }))}
        />
        <Selector etiqueta="Agrupar" valor={por} onCambio={setPor} opciones={AGRUPACIONES} />
        <div className="flex w-56 flex-col gap-3">
          <Label className="text-xs font-bold uppercase">{bins} intervalos</Label>
          <Slider
            value={[bins]}
            min={5}
            max={50}
            step={1}
            disabled={variable === "magnitud"}
            onValueChange={(valor) => setBins(valor[0])}
            aria-label="Número de intervalos"
          />
        </div>
        <Interruptor etiqueta="Solo sequía" activo={soloDr} onCambio={setSoloDr} />
      </div>
      <Contenido consulta={consulta} alto="h-80" esVacio={(d) => d.grupos.length === 0}>
        {(datos) => {
          const filas = datos.bordes.slice(0, -1).map((borde, i) => {
            const centro = (borde + datos.bordes[i + 1]) / 2
            const fila: FilaGrafico = {
              intervalo: variable === "magnitud" ? String(Math.round(centro)) : formatoBorde(centro),
            }
            for (const grupo of datos.grupos) fila[grupo.grupo] = grupo.conteos[i]
            return fila
          })
          const series = datos.grupos.map((grupo, i) => ({
            clave: grupo.grupo,
            nombre: grupo.etiqueta,
            color: por === "ninguno" ? PALETA.principal : listas[por] ? colorCategoria(listas[por], grupo.grupo) : colorSerie(i),
          }))
          return (
            <GraficoBarras
              datos={filas}
              categoria="intervalo"
              series={series}
              apilado
              zoom
              alto={360}
              formato={(v) => entero(v)}
              etiquetaX={etiquetaVariable(variable)}
              etiquetaY="Registros"
            />
          )
        }}
      </Contenido>
    </div>
  )
}

function Dispersion() {
  const etiquetaVariable = useEtiquetasVariables()
  const etiquetas = useEtiquetas()
  const [x, setX] = useState<VariableNumerica>("exceso_verde")
  const [soloDr, setSoloDr] = useState(true)
  const consulta = useDispersion(x, soloDr)

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-end gap-4">
        <Selector
          etiqueta="Eje X"
          valor={x}
          onCambio={setX}
          opciones={VARIABLES_NUMERICAS.filter((v) => v !== "magnitud").map((v) => ({ valor: v, etiqueta: etiquetaVariable(v) }))}
        />
        <Interruptor etiqueta="Solo sequía" activo={soloDr} onCambio={setSoloDr} />
      </div>
      <Contenido consulta={consulta} alto="h-80" esVacio={(d) => d.puntos.length === 0}>
        {(datos) => {
          const clave = soloDr ? "temporada" : "dano"
          const lista = soloDr ? etiquetas.catalogos?.temporadas : etiquetas.catalogos?.danos
          const grupos = (lista ?? [])
            .map((opcion) => ({
              nombre: opcion.nombre,
              color: colorCategoria(lista, opcion.codigo),
              puntos: datos.puntos.filter((p) => p[clave] === opcion.codigo).map((p) => ({ x: p.x, y: p.y })),
            }))
            .filter((grupo) => grupo.puntos.length > 0)
          return (
            <>
              <GraficoDispersion grupos={grupos} etiquetaX={etiquetaVariable(x)} etiquetaY="Magnitud" />
              <p className="text-xs text-muted-foreground">
                Muestra de {entero(datos.puntos.length)} de {entero(datos.total_disponible)} registros. Pulse la leyenda para ocultar grupos.
              </p>
            </>
          )
        }}
      </Contenido>
    </div>
  )
}

function Correlaciones() {
  const etiquetaVariable = useEtiquetasVariables()
  const [soloDr, setSoloDr] = useState(true)
  const consulta = useCorrelaciones(soloDr)
  return (
    <div className="flex flex-col gap-4">
      <Interruptor etiqueta="Solo sequía" activo={soloDr} onCambio={setSoloDr} />
      <Contenido consulta={consulta} alto="h-80" esVacio={(d) => d.every((c) => c.spearman === null)}>
        {(datos) => {
          const filas = datos
            .filter((c) => c.spearman !== null)
            .sort((a, b) => (b.spearman ?? 0) - (a.spearman ?? 0))
            .map((c) => ({ variable: etiquetaVariable(c.variable), spearman: c.spearman, n: c.n }))
          return (
            <>
              <GraficoBarras
                datos={filas}
                categoria="variable"
                series={[{ clave: "spearman", nombre: "Spearman", color: PALETA.principal }]}
                horizontal
                alto={Math.max(260, filas.length * 30)}
                anchoCategoria={170}
                colorBarra={(fila) => (Number(fila.spearman) >= 0 ? PALETA.principal : PALETA.terciario)}
                formato={(v) => numero(v, 2)}
                etiquetaX="Coeficiente con la magnitud"
              />
              <p className="text-xs text-muted-foreground">
                Verde indica relación positiva y terracota relación negativa. Se calcula sobre {entero(datos[0]?.n ?? 0)} registros.
              </p>
            </>
          )
        }}
      </Contenido>
    </div>
  )
}

export default function Explorar() {
  const resumen = useResumen()
  return (
    <>
      <Encabezado
        etiqueta="Requisito a"
        titulo="Explorar datos"
        descripcion="Distribución de las variables del conjunto de modelado, relación de los atributos de imagen con la magnitud del daño y consulta de registros individuales."
      />
      <div className="grid gap-6">
        <div className="grid gap-6 xl:grid-cols-2">
          <Bloque titulo="Composición del conjunto" descripcion="Registros por magnitud, temporada, tipo de daño y etapa de crecimiento.">
            <Contenido consulta={resumen} alto="h-80">
              {(datos) => <ResumenConteos resumen={datos} />}
            </Contenido>
          </Bloque>
          <Bloque titulo="Variables" descripcion="Variables del conjunto y modelos que las usan como entrada.">
            <TablaVariables />
          </Bloque>
        </div>
        <Bloque titulo="Histograma" descripcion="Distribución de una variable, apilada por grupo. Arrastre el control inferior para acercar.">
          <Histograma />
        </Bloque>
        <div className="grid gap-6 xl:grid-cols-2">
          <Bloque titulo="Dispersión contra la magnitud" descripcion="Cada punto es una fotografía.">
            <Dispersion />
          </Bloque>
          <Bloque titulo="Correlación de Spearman" descripcion="Relación monótona de cada atributo con la magnitud.">
            <Correlaciones />
          </Bloque>
        </div>
        <Bloque titulo="Registros" descripcion="Filtre, ordene por columna y abra cualquier registro para ver su fotografía.">
          <TablaRegistros />
        </Bloque>
      </div>
    </>
  )
}
