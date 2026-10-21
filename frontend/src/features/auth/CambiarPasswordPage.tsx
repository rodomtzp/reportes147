import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../app/AuthContext";
import { CampoPassword } from "../../shared/components/CampoPassword";
import { cambiarPassword } from "./api";

export function CambiarPasswordPage() {
  const { usuario, recargar, salir } = useAuth();
  const navegar = useNavigate();
  const [actual, setActual] = useState("");
  const [nueva, setNueva] = useState("");
  const [confirmacion, setConfirmacion] = useState("");
  const [error, setError] = useState("");
  const [enviando, setEnviando] = useState(false);
  const obligatorio = !!usuario?.debe_cambiar_password;

  async function enviar(e: FormEvent) {
    e.preventDefault();
    setError("");
    if (nueva !== confirmacion) return setError("La confirmación no coincide con la nueva contraseña.");
    setEnviando(true);
    try {
      await cambiarPassword(actual, nueva);
      await recargar();
      navegar("/", { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo cambiar la contraseña");
    } finally {
      setEnviando(false);
    }
  }

  const noCoincide = confirmacion.length > 0 && nueva !== confirmacion;

  return (
    <main className="contenido auth-centrado">
      <form onSubmit={enviar} className="acceso-tarjeta">
        <h1>Cambiar contraseña</h1>
        {obligatorio && (
          <p className="aviso">Ingresaste con una contraseña temporal. Define una nueva para continuar.</p>
        )}
        <CampoPassword etiqueta="Contraseña actual" valor={actual} onCambio={setActual} autoComplete="current-password" />
        <CampoPassword etiqueta="Nueva contraseña" valor={nueva} onCambio={setNueva} autoComplete="new-password"
          minLength={10} ayuda="Mínimo 10 caracteres. Debe ser distinta de la actual." />
        <CampoPassword etiqueta="Confirmar nueva contraseña" valor={confirmacion} onCambio={setConfirmacion} autoComplete="new-password"
          invalido={noCoincide} ayuda={noCoincide ? "No coincide con la nueva contraseña." : undefined} />
        {error && <p className="error" role="alert">{error}</p>}
        <div className="fila-botones">
          <button type="submit" disabled={enviando}>{enviando ? "Guardando…" : "Cambiar contraseña"}</button>
          {obligatorio && <button type="button" className="secundario" onClick={salir}>Cerrar sesión</button>}
        </div>
      </form>
    </main>
  );
}
