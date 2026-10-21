export const GRAVEDADES: { valor: string; etiqueta: string }[] = [
  { valor: "LEVE", etiqueta: "Leve" },
  { valor: "MEDIA", etiqueta: "Media" },
  { valor: "GRAVE", etiqueta: "Grave" },
  { valor: "MUY_GRAVE", etiqueta: "Muy grave" },
];
export const ESTADOS: { valor: string; etiqueta: string }[] = [
  { valor: "EN_REVISION_ORIENTACION", etiqueta: "En revisión por Orientación" },
  { valor: "ATENDIDO_SUBDIRECCION", etiqueta: "Atendido por Subdirección" },
  { valor: "SANCIONADO_CONCLUIDO", etiqueta: "Sancionado / Concluido" },
];
export const ESTADOS_LLAMADA: Record<string, string> = {
  PENDIENTE: "Pendiente", REALIZADA: "Realizada", NO_CONTESTO: "No contestó", ATENDIDA: "Atendida",
};

export const etiquetaGravedad = (v: string) => GRAVEDADES.find((g) => g.valor === v)?.etiqueta ?? v;
export const etiquetaEstado = (v: string) => ESTADOS.find((e) => e.valor === v)?.etiqueta ?? (v === "CREADO" ? "Creado" : v);

export const fechaLocal = (iso: string | null) => (iso ? new Date(iso).toLocaleString("es-MX", { dateStyle: "medium", timeStyle: "short" }) : "—");

/** ISO → valor para <input type="datetime-local"> en la hora local del navegador. */
export function aInputLocal(iso: string): string {
  const d = new Date(iso);
  const p = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}T${p(d.getHours())}:${p(d.getMinutes())}`;
}

export interface TipoIncidencia { id: number; nombre: string; activo: boolean; es_otro: boolean }

export interface ReporteFila {
  id: number; folio: string; incidente_id: string; estudiante_id: number; estudiante: string; numero_control: string;
  grupo: string | null; carrera: string | null; tipo_incidencia_id: number; tipo_incidencia: string; descripcion_otro: string | null;
  resumen: string; gravedad: string; estado: string; estado_llamada: string; fecha_hora_incidente: string; creado_en: string; creado_por: string; cancelado: boolean;
}

export interface Llamada {
  id: number; estado: string; tutor_legal_id: number; tutor: string; parentesco: string | null;
  atendio_nombre: string | null; observaciones: string | null; fecha_hora: string | null; realizado_por: string | null;
}
export interface MensajeWA { id: number; tutor: string; texto: string; generado_por: string; generado_en: string; enviado_en: string | null }
export interface Seguimiento {
  folio: string; estudiante: string; estado_llamada: string;
  tutores: { id: number; nombre: string; parentesco: string | null; telefono: string; es_principal: boolean }[];
  llamadas: Llamada[]; mensajes: MensajeWA[];
}

export interface ReporteDetalle extends ReporteFila {
  llamadas: Llamada[] | null; mensajes_whatsapp: MensajeWA[] | null;
  sancion: SancionInfo | null;
  acumulacion: { ciclo: number; total: number; umbral: number; listo_para_sancion: boolean } | null;
  descripcion: string; motivo_cancelacion: string | null; cancelado_por: string | null; cancelado_en: string | null;
  adjuntos: { id: number; nombre: string; tipo: string; tamano: number; subido_en: string }[];
  historial: { id: number; tipo: string; campo: string | null; valor_anterior: string | null; valor_nuevo: string | null; comentario: string | null; usuario: string; fecha: string }[];
  relacionados: { id: number; folio: string; estudiante: string; grupo: string | null; gravedad: string; cancelado: boolean }[];
}

export interface SancionInfo {
  id: number; origen: "DIRECTA" | "ACUMULACION"; tipo: string; tipo_sancion_id: number; dias: number | null;
  observaciones: string | null; aplicada_por: string; aplicada_en: string; folios: string[];
}
export interface TipoSancion { id: number; nombre: string; requiere_dias: boolean; activo: boolean }
export interface CicloExpediente {
  numero: number; abierto: boolean; fecha_inicio: string; fecha_cierre: string | null; contables: number;
  listo_para_sancion: boolean; sancion: SancionInfo | null;
  reportes: (ReporteFila & { cuenta: boolean })[];
}
export interface Expediente {
  estudiante_id: number; estudiante: string; numero_control: string; grupo_actual: string | null;
  total_reportes: number; umbral: number; ciclo_actual: CicloExpediente | null;
  ciclos_anteriores: CicloExpediente[]; sanciones_directas: SancionInfo[];
}
