import { api, tokens } from "../../shared/api/client";

export interface UsuarioActual {
  id: number;
  nombre: string;
  correo: string;
  roles: string[];
  permisos: string[];
  debe_cambiar_password: boolean;
  grupos_tutelados: string[];
}

export async function iniciarSesion(correo: string, password: string): Promise<UsuarioActual> {
  const t = await api<{ access_token: string; refresh_token: string }>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ correo, password }),
  });
  tokens.guardar(t.access_token, t.refresh_token);
  return obtenerUsuarioActual();
}

export const obtenerUsuarioActual = () => api<UsuarioActual>("/auth/me");

/** Cambiar la contraseña cierra las demás sesiones: el servidor devuelve tokens nuevos para esta. */
export async function cambiarPassword(password_actual: string, password_nueva: string): Promise<void> {
  const r = await api<{ mensaje: string; access_token: string; refresh_token: string }>("/auth/cambiar-password", {
    method: "POST",
    body: JSON.stringify({ password_actual, password_nueva }),
  });
  tokens.guardar(r.access_token, r.refresh_token);
}
