import { Campo, Columna, CrudPage, etiquetaDe, si_no } from "../../shared/components/CrudPage";

const campos: Campo[] = [
  {
    nombre: "carrera_id", etiqueta: "Carrera", tipo: "select", requerido: true,
    opcionesDe: { ruta: "/carreras", valor: "id", etiqueta: (c) => c.nombre },
  },
  { nombre: "semestre", etiqueta: "Semestre (1-6)", tipo: "numero", requerido: true, min: 1, max: 6 },
  { nombre: "letra", etiqueta: "Letra", tipo: "texto", requerido: true, maxLength: 1 },
  { nombre: "activo", etiqueta: "Activo", tipo: "booleano", soloEdicion: true },
];
const columnas: Columna[] = [
  { titulo: "Grupo", valor: (f) => f.clave },
  { titulo: "Carrera", valor: (f, o) => etiquetaDe(o, "carrera_id", f.carrera_id) },
  { titulo: "Activo", valor: (f) => si_no(f.activo) },
];

export function GruposPage() {
  return <CrudPage titulo="Grupos" ruta="/grupos" campos={campos} columnas={columnas} />;
}
