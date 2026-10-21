import { FormEvent, useId, useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../../app/AuthContext";
import { CampoPassword } from "../../shared/components/CampoPassword";

const ETAPAS = ["Creado", "En revisión por Orientación", "Atendido por Subdirección", "Concluido"];

export function LoginPage() {
  const { usuario, entrar } = useAuth();
  const navegar = useNavigate();
  const idCorreo = useId();
  const [correo, setCorreo] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [enviando, setEnviando] = useState(false);

  if (usuario) return <Navigate to="/" replace />;

  async function enviar(e: FormEvent) {
    e.preventDefault();
    setError("");
    setEnviando(true);
    try {
      await entrar(correo.trim(), password);
      navegar("/", { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo iniciar sesión");
    } finally {
      setEnviando(false);
    }
  }

  return (
    <main className="acceso">
      <aside className="acceso-marca">
        <div>
          <p className="acceso-plantel">CBTis 147</p>
          <p className="acceso-titulo">Control de reportes</p>
          <p className="acceso-desc">Registro, seguimiento y sanciones de los reportes del plantel, en un solo lugar.</p>
        </div>
        <figure className="papeleta" aria-label="Así avanza un reporte">
          <figcaption>Así avanza un reporte</figcaption>
          <p className="papeleta-folio">RPT-2026-0001</p>
          <ol className="papeleta-etapas">
            {ETAPAS.map((e, i) => (
              <li key={e} className={i < 2 ? "hecha" : ""} aria-current={i === 1 ? "step" : undefined}>{e}</li>
            ))}
          </ol>
        </figure>
      </aside>

      <section className="acceso-formulario">
        <form onSubmit={enviar} className="acceso-tarjeta">
          <h1>Iniciar sesión</h1>
          <p className="acceso-sub">Usa el correo con el que te dieron de alta.</p>
          <div className="campo">
            <label htmlFor={idCorreo}>Correo</label>
            <input id={idCorreo} type="email" value={correo} onChange={(e) => setCorreo(e.target.value)} required autoFocus
              autoComplete="username" inputMode="email" aria-invalid={error ? true : undefined} />
          </div>
          <CampoPassword etiqueta="Contraseña" valor={password} onCambio={setPassword} autoComplete="current-password" invalido={!!error} />
          {error && <p className="error" role="alert">{error}</p>}
          <button type="submit" className="boton-ancho" disabled={enviando}>{enviando ? "Entrando…" : "Entrar"}</button>
          <p className="ayuda">¿No puedes entrar? Pide a Orientación o al Administrador que restablezca tu contraseña.</p>
        </form>
      </section>
    </main>
  );
}
