import { api } from "../../shared/api/client";
import { Campo, Columna, CrudPage, si_no } from "../../shared/components/CrudPage";

const campos: Campo[] = [
  { nombre: "nombre", etiqueta: "Nombre (ej. 2026-A)", tipo: "texto", requerido: true, maxLength: 30 },
  { nombre: "fecha_inicio", etiqueta: "Inicio", tipo: "fecha", requerido: true },
  { nombre: "fecha_fin", etiqueta: "Fin", tipo: "fecha", requerido: true },
];
const columnas: Columna[] = [
  { titulo: "Periodo", valor: (f) => f.nombre },
  { titulo: "Inicio", valor: (f) => f.fecha_inicio },
  { titulo: "Fin", valor: (f) => f.fecha_fin },
  { titulo: "Vigente", valor: (f) => si_no(f.vigente) },
];

export function PeriodosPage() {
  return (
    <CrudPage
      titulo="Periodos escolares"
      ruta="/periodos"
      campos={campos}
      columnas={columnas}
      acciones={(fila, recargar) =>
        !fila.vigente && (
          <button
            onClick={async () => {
              await api(`/periodos/${fila.id}/vigente`, { method: "POST" });
              recargar();
            }}
          >
            Hacer vigente
          </button>
        )
      }
    />
  );
}
