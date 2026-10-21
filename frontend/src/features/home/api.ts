import { api } from "../../shared/api/client";

export interface Par { etiqueta: string; valor: number }
export interface EnRiesgo { estudiante_id: number; estudiante: string; grupo: string | null; total: number }

export type Rango = "periodo" | "mes" | "30dias";

export interface Dashboard {
  rango: Rango;
  desde: string;
  hasta: string;
  granularidad: "dia" | "semana";
  periodo: string | null;
  alcance: "total" | "propio" | "ninguno";
  total_rango: number;
  mes_actual: number;
  mes_anterior: number;
  por_gravedad: Par[];
  pendientes_llamada: number | null;
  alertas_pendientes: number | null;
  en_riesgo: EnRiesgo[];
  total_en_riesgo: number;
  listos_para_sancion: number;
  serie: Par[];
  por_grupo: Par[];
  por_carrera: Par[];
  por_tipo: Par[];
  por_estado: Par[];
}

export const obtenerDashboard = (rango: Rango) => api<Dashboard>(`/dashboard?rango=${rango}`);
