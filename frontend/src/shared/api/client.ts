const BASE = "/api/v1";
const KEY_ACCESS = "access_token";
const KEY_REFRESH = "refresh_token";

export const tokens = {
  guardar(access: string, refresh?: string) {
    sessionStorage.setItem(KEY_ACCESS, access);
    if (refresh) sessionStorage.setItem(KEY_REFRESH, refresh);
  },
  access: () => sessionStorage.getItem(KEY_ACCESS),
  refresh: () => sessionStorage.getItem(KEY_REFRESH),
  limpiar() {
    sessionStorage.removeItem(KEY_ACCESS);
    sessionStorage.removeItem(KEY_REFRESH);
  },
};

export class ApiError extends Error {
  constructor(public status: number, message: string, public codigo?: string) {
    super(message);
  }
}

async function renovarAccess(): Promise<boolean> {
  const refresh = tokens.refresh();
  if (!refresh) return false;
  const r = await fetch(`${BASE}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refresh }),
  });
  if (!r.ok) return false;
  tokens.guardar((await r.json()).access_token);
  return true;
}

/** Petición autenticada; renueva el access token una vez si expiró. */
async function peticion(ruta: string, init: RequestInit = {}, reintento = true): Promise<Response> {
  const headers = new Headers(init.headers);
  // Con FormData el navegador define el Content-Type (multipart) por su cuenta.
  if (init.body && !(init.body instanceof FormData)) headers.set("Content-Type", "application/json");
  const access = tokens.access();
  if (access) headers.set("Authorization", `Bearer ${access}`);
  const r = await fetch(`${BASE}${ruta}`, { ...init, headers });
  if (r.status === 401 && reintento && tokens.refresh() && (await renovarAccess())) {
    return peticion(ruta, init, false);
  }
  if (!r.ok) {
    const cuerpo = await r.json().catch(() => ({}));
    throw new ApiError(r.status, cuerpo.error ?? "Error de red", cuerpo.codigo);
  }
  return r;
}

export async function api<T>(ruta: string, init: RequestInit = {}): Promise<T> {
  return (await peticion(ruta, init)).json() as Promise<T>;
}

/** Descarga un archivo protegido (el enlace directo no enviaría el token). */
export async function descargar(ruta: string, nombreArchivo: string): Promise<void> {
  const blob = await (await peticion(ruta)).blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = nombreArchivo;
  a.click();
  URL.revokeObjectURL(url);
}
