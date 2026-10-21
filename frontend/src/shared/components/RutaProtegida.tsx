import { ReactNode } from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../../app/AuthContext";

interface Props {
  children: ReactNode;
  permiso?: string;
  /** Permite entrar aunque el usuario tenga una contraseña temporal pendiente de cambio. */
  permitirPasswordPendiente?: boolean;
}

export function RutaProtegida({ children, permiso, permitirPasswordPendiente = false }: Props) {
  const { usuario, cargando, puede } = useAuth();
  if (cargando) return <p>Cargando…</p>;
  if (!usuario) return <Navigate to="/login" replace />;
  if (usuario.debe_cambiar_password && !permitirPasswordPendiente) {
    return <Navigate to="/cambiar-password" replace />;
  }
  if (permiso && !puede(permiso)) return <p>No tienes acceso a esta sección.</p>;
  return <>{children}</>;
}
