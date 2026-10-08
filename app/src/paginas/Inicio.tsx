import { ArrowRight, CheckCircle2, XCircle } from "lucide-react"
import { Link } from "react-router"

import type { Salud } from "@/api/cliente"
import { useResumen, useSalud } from "@/api/consultas"
import { Bloque } from "@/components/Bloque"
import { Encabezado } from "@/components/Encabezado"
import { EscalaMagnitud } from "@/components/EscalaMagnitud"
import { AvisoError, Cargando } from "@/components/Estados"
import { Metrica } from "@/components/Metrica"
import { SECCIONES } from "@/components/navegacion"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { entero, plural, porcentaje } from "@/lib/formato"

function Indicador({ activo, texto }: { activo: boolean; texto: string }) {
  const Icono = activo ? CheckCircle2 : XCircle
  return (
    <li className="flex items-center gap-2">
      <Icono className={activo ? "size-5 text-primary" : "size-5 text-destructive"} />
      <span>{texto}</span>
    </li>
  )
}

function EstadoSistema({ salud, desactualizado }: { salud: Salud; desactualizado: boolean }) {
  return (
    <div className="flex flex-col gap-4">
      {desactualizado && (
        <Alert status="warning">
          <AlertTitle className="font-head">Sin conexión</AlertTitle>
          <AlertDescription>Se muestra la última lectura conocida; la API no responde ahora.</AlertDescription>
        </Alert>
      )}
      <ul className="flex flex-col gap-2 text-sm">
        <Indicador
          activo={!desactualizado}
          texto={desactualizado ? `API sin conexión ahora, última versión conocida ${salud.version}` : `API en línea, versión ${salud.version}`}
        />
        <Indicador activo={salud.datos_disponibles} texto={salud.datos_disponibles ? "Conjunto de modelado disponible" : "Sin conjunto de modelado"} />
        <Indicador
          activo={salud.modelos_disponibles.length > 0}
          texto={`${plural(salud.modelos_disponibles.length, "modelo entrenado", "modelos entrenados")} para predecir`}
        />
        <Indicador
          activo={salud.modelos_con_resultados.length > 0}
          texto={`${plural(salud.modelos_con_resultados.length, "modelo", "modelos")} con resultados de prueba`}
        />
      </ul>
      {!salud.datos_disponibles && (
        <Alert status="warning">
          <AlertTitle className="font-head">Faltan datos</AlertTitle>
          <AlertDescription>
            Ejecute «python -m src.conjunto» para crear el conjunto, o levante el backend de demostración con «python -m
            src.demo».
          </AlertDescription>
        </Alert>
      )}
      {salud.modelos_disponibles.length === 0 && (
        <Alert status="warning">
          <AlertTitle className="font-head">Faltan modelos</AlertTitle>
          <AlertDescription>
            Entrene al menos un modelo y guarde su artefacto en data/procesado/modelos/ para habilitar la predicción.
          </AlertDescription>
        </Alert>
      )}
    </div>
  )
}

function Totales() {
  const resumen = useResumen()
  if (resumen.isPending) return <Cargando alto="h-28" />
  if (!resumen.data) return <AvisoError error={resumen.error} />
  const { total_registros, registros_dr, campos, por_subconjunto } = resumen.data
  const conteo = (clave: string) => por_subconjunto.find((c) => c.clave === clave)?.conteo ?? 0
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <Metrica etiqueta="Registros" valor={entero(total_registros)} detalle="Fotografías con atributos calculados" />
      <Metrica
        etiqueta="Registros con sequía"
        valor={entero(registros_dr)}
        detalle={`${porcentaje(registros_dr, total_registros)} del conjunto`}
        className="bg-accent"
      />
      <Metrica etiqueta="Campos" valor={entero(campos)} detalle="Parcelas distintas" />
      <Metrica
        etiqueta="Entrenamiento / prueba"
        valor={`${entero(conteo("entrenamiento"))} / ${entero(conteo("prueba"))}`}
        detalle="Partición agrupada por campo"
      />
    </div>
  )
}

export default function Inicio() {
  const salud = useSalud()
  return (
    <>
      <Encabezado
        etiqueta="CGIAR Eyes on the Ground"
        titulo="Magnitud del daño por sequía"
        descripcion="Exploración de las fotografías de pequeños productores, comparación de modelos y estimación de la severidad del daño a partir de una imagen."
      />
      <div className="grid gap-6 lg:grid-cols-[2fr_1fr]">
        <div className="flex flex-col gap-6">
          {salud.data?.datos_disponibles && <Totales />}
          <div className="grid gap-4 sm:grid-cols-2">
            {SECCIONES.slice(1).map(({ ruta, titulo, descripcion, icono: Icono }) => (
              <Link
                key={ruta}
                to={ruta}
                className="group flex flex-col gap-3 border-2 bg-card p-5 shadow-md transition-all hover:-translate-x-0.5 hover:-translate-y-0.5 hover:shadow-lg"
              >
                <span className="flex size-11 items-center justify-center border-2 bg-secondary shadow-sm">
                  <Icono className="size-6" />
                </span>
                <span className="font-head text-xl">{titulo}</span>
                <span className="text-sm text-muted-foreground">{descripcion}</span>
                <span className="mt-auto flex items-center gap-1 font-head text-sm group-hover:underline">
                  Abrir <ArrowRight className="size-4" />
                </span>
              </Link>
            ))}
          </div>
        </div>
        <div className="flex flex-col gap-6">
          <Bloque titulo="Estado del sistema">
            {salud.isPending && <Cargando alto="h-32" />}
            {salud.isError && !salud.data && <AvisoError error={salud.error} />}
            {salud.data && <EstadoSistema salud={salud.data} desactualizado={salud.isError} />}
          </Bloque>
          <Bloque titulo="Escala de magnitud" descripcion="Porcentaje del cultivo dañado por sequía. El color siempre acompaña al número.">
            <EscalaMagnitud />
          </Bloque>
          <Button asChild variant="secondary" className="w-full">
            <Link to="/predecir">Predecir una fotografía</Link>
          </Button>
        </div>
      </div>
    </>
  )
}
