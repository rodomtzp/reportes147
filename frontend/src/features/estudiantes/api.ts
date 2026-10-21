export interface Tutor { id: number; nombre: string; parentesco: string | null; telefono: string; correo: string | null; es_principal: boolean }
export interface Detalle {
  id: number; numero_control: string; primer_apellido: string; segundo_apellido: string | null; nombres: string;
  nombre_completo: string; telefono: string | null; correo: string | null; calle: string | null; numero: string | null;
  colonia: string | null; ciudad: string | null; generacion: string; estatus: string;
  grupo_actual: string | null; carrera_actual: string | null;
  tutores_legales: Tutor[]; historial: { periodo: string; grupo: string; semestre: number; carrera: string }[];
}
export interface Grupo { id: number; clave: string; carrera_id: number; activo: boolean }
export const ESTATUS = ["ACTIVO", "BAJA", "EGRESADO"];
