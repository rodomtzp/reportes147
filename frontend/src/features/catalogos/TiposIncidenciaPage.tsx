import { Campo, Columna, CrudPage, si_no } from "../../shared/components/CrudPage";

const campos: Campo[] = [
  { nombre: "nombre", etiqueta: "Nombre", tipo: "texto", requerido: true, maxLength: 100 },
  { nombre: "activo", etiqueta: "Activo", tipo: "booleano", soloEdicion: true },
];
const columnas: Columna[] = [
  { titulo: "Incidencia", valor: (f) => (f.es_otro ? `${f.nombre} (permite texto libre)` : f.nombre) },
  { titulo: "Activa", valor: (f) => si_no(f.activo) },
];

export function TiposIncidenciaPage() {
  return (
    <CrudPage
      titulo="Tipos de incidencia"
      ruta="/tipos-incidencia"
      campos={campos}
      columnas={columnas}
      puedeEditar={(f) => !f.es_otro}
    />
  );
}
