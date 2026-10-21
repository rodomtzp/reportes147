import { createContext, ReactNode, useCallback, useContext, useEffect, useState } from "react";
import { tokens } from "../shared/api/client";
import { iniciarSesion, obtenerUsuarioActual, UsuarioActual } from "../features/auth/api";

interface AuthState {
  usuario: UsuarioActual | null;
  cargando: boolean;
  entrar: (correo: string, password: string) => Promise<void>;
  salir: () => void;
  recargar: () => Promise<void>;
  puede: (permiso: string) => boolean;
}

const Ctx = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [usuario, setUsuario] = useState<UsuarioActual | null>(null);
  const [cargando, setCargando] = useState(true);

  useEffect(() => {
    if (!tokens.access()) {
      setCargando(false);
      return;
    }
    obtenerUsuarioActual()
      .then(setUsuario)
      .catch(() => tokens.limpiar())
      .finally(() => setCargando(false));
  }, []);

  const entrar = useCallback(async (correo: string, password: string) => {
    setUsuario(await iniciarSesion(correo, password));
  }, []);

  const salir = useCallback(() => {
    tokens.limpiar();
    setUsuario(null);
  }, []);

  const recargar = useCallback(async () => {
    setUsuario(await obtenerUsuarioActual());
  }, []);

  // Solo para mostrar u ocultar elementos; la autorización real la hace el servidor.
  const puede = useCallback((p: string) => !!usuario?.permisos.includes(p), [usuario]);

  return <Ctx.Provider value={{ usuario, cargando, entrar, salir, recargar, puede }}>{children}</Ctx.Provider>;
}

export function useAuth(): AuthState {
  const v = useContext(Ctx);
  if (!v) throw new Error("useAuth debe usarse dentro de AuthProvider");
  return v;
}
