import { Campo, Columna, CrudPage, si_no } from "../../shared/components/CrudPage";

const campos: Campo[] = [
  { nombre: "nombre", etiqueta: "Nombre", tipo: "texto", requerido: true, maxLength: 100 },
  { nombre: "requiere_dias", etiqueta: "Requiere número de días", tipo: "booleano" },
  { nombre: "activo", etiqueta: "Activa", tipo: "booleano", soloEdicion: true },
];
const columnas: Columna[] = [
  { titulo: "Sanción", valor: (f) => f.nombre },
  { titulo: "Requiere días", valor: (f) => si_no(f.requiere_dias) },
  { titulo: "Activa", valor: (f) => si_no(f.activo) },
];

export function TiposSancionPage() {
  return <CrudPage titulo="Tipos de sanción" ruta="/tipos-sancion" campos={campos} columnas={columnas} />;
}
