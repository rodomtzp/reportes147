import { Campo, Columna, CrudPage } from "../../shared/components/CrudPage";

const campos: Campo[] = [
  {
    nombre: "periodo_id", etiqueta: "Periodo", tipo: "select", requerido: true,
    opcionesDe: { ruta: "/periodos", valor: "id", etiqueta: (p) => p.nombre },
  },
  {
    nombre: "grupo_id", etiqueta: "Grupo", tipo: "select", requerido: true,
    opcionesDe: { ruta: "/grupos?solo_activos=true", valor: "id", etiqueta: (g) => g.clave },
  },
  {
    nombre: "usuario_id", etiqueta: "Docente (tutor)", tipo: "select", requerido: true,
    opcionesDe: { ruta: "/usuarios?rol=DOCENTE&activo=true", valor: "id", etiqueta: (u) => u.nombre },
  },
];
const columnas: Columna[] = [
  { titulo: "Periodo", valor: (f) => f.periodo_nombre },
  { titulo: "Grupo", valor: (f) => `${f.grupo_clave} – ${f.carrera_nombre}` },
  { titulo: "Tutor", valor: (f) => f.usuario_nombre },
];

export function TutoresPage() {
  return (
    <CrudPage
      titulo="Asignación de tutores"
      ruta="/asignaciones-tutor"
      campos={campos}
      columnas={columnas}
      editable={false}
      eliminable
    />
  );
}
