import { Campo, Columna, CrudPage, si_no } from "../../shared/components/CrudPage";

const campos: Campo[] = [
  { nombre: "nombre", etiqueta: "Nombre", tipo: "texto", requerido: true, maxLength: 150 },
  { nombre: "clave", etiqueta: "Clave", tipo: "texto", requerido: true, maxLength: 20 },
  { nombre: "activa", etiqueta: "Activa", tipo: "booleano", soloEdicion: true },
];
const columnas: Columna[] = [
  { titulo: "Clave", valor: (f) => f.clave },
  { titulo: "Nombre", valor: (f) => f.nombre },
  { titulo: "Activa", valor: (f) => si_no(f.activa) },
];

export function CarrerasPage() {
  return <CrudPage titulo="Carreras" ruta="/carreras" campos={campos} columnas={columnas} />;
}
