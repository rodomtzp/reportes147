import { FormEvent, useCallback, useEffect, useState } from "react";
import { useAuth } from "../../app/AuthContext";
import { api } from "../../shared/api/client";

interface Usuario {
  id: number;
  nombre: string;
  correo: string;
  roles: string[];
  activo: boolean;
  debe_cambiar_password: boolean;
}

const ROLES: { valor: string; etiqueta: string }[] = [
  { valor: "DOCENTE", etiqueta: "Docente" },
  { valor: "PREFECTO", etiqueta: "Prefecto" },
  { valor: "ORIENTACION", etiqueta: "Orientación Educativa" },
  { valor: "SUBDIRECCION", etiqueta: "Subdirección" },
  { valor: "DIRECCION", etiqueta: "Dirección" },
  { valor: "ADMINISTRADOR", etiqueta: "Administrador" },
];
const etiquetaRol = (v: string) => ROLES.find((r) => r.valor === v)?.etiqueta ?? v;

const FORM_VACIO = { nombre: "", correo: "", roles: [] as string[], activo: true };

export function UsuariosPage() {
  const { usuario: yo } = useAuth();
  const [usuarios, setUsuarios] = useState<Usuario[]>([]);
  const [form, setForm] = useState(FORM_VACIO);
  const [editandoId, setEditandoId] = useState<number | null>(null);
  const [temporal, setTemporal] = useState<{ correo: string; password: string } | null>(null);
  const [error, setError] = useState("");

  const cargar = useCallback(async () => {
    try {
      setUsuarios(await api<Usuario[]>("/usuarios"));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al cargar");
    }
  }, []);
  useEffect(() => { cargar(); }, [cargar]);

  function alternarRol(rol: string) {
    setForm((f) => ({ ...f, roles: f.roles.includes(rol) ? f.roles.filter((r) => r !== rol) : [...f.roles, rol] }));
  }

  function cancelar() {
    setEditandoId(null);
    setForm(FORM_VACIO);
  }

  async function enviar(e: FormEvent) {
    e.preventDefault();
    setError("");
    if (form.roles.length === 0) return setError("Selecciona al menos un rol.");
    try {
      if (editandoId === null) {
        const r = await api<{ usuario: Usuario; password_temporal: string }>("/usuarios", {
          method: "POST",
          body: JSON.stringify({ nombre: form.nombre, correo: form.correo, roles: form.roles }),
        });
        setTemporal({ correo: r.usuario.correo, password: r.password_temporal });
      } else {
        await api(`/usuarios/${editandoId}`, {
          method: "PATCH",
          body: JSON.stringify({ nombre: form.nombre, roles: form.roles, activo: form.activo }),
        });
      }
      cancelar();
      await cargar();
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo guardar");
    }
  }

  async function restablecer(u: Usuario) {
    if (!window.confirm(`¿Generar una nueva contraseña temporal para ${u.nombre}?`)) return;
    setError("");
    try {
      const r = await api<{ password_temporal: string }>(`/usuarios/${u.id}/restablecer-password`, { method: "POST" });
      setTemporal({ correo: u.correo, password: r.password_temporal });
      await cargar();
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo restablecer");
    }
  }

  return (
    <section>
      <h1>Usuarios</h1>

      {temporal && (
        <div className="aviso" role="status">
          Contraseña temporal para <strong>{temporal.correo}</strong>: <code>{temporal.password}</code>
          <br />
          Entrégala al usuario por un medio seguro. No volverá a mostrarse y deberá cambiarla al entrar.{" "}
          <button className="secundario" onClick={() => setTemporal(null)}>Entendido</button>
        </div>
      )}

      <form className="formulario" onSubmit={enviar}>
        <label>
          Nombre completo
          <input value={form.nombre} onChange={(e) => setForm({ ...form, nombre: e.target.value })} required minLength={2} maxLength={150} />
        </label>
        <label>
          Correo
          <input type="email" value={form.correo} disabled={editandoId !== null} onChange={(e) => setForm({ ...form, correo: e.target.value })} required />
        </label>
        <div>
          Roles
          <div className="roles">
            {ROLES.map((r) => (
              <label key={r.valor}>
                <input type="checkbox" checked={form.roles.includes(r.valor)} onChange={() => alternarRol(r.valor)} />
                {r.etiqueta}
              </label>
            ))}
          </div>
        </div>
        {editandoId !== null && (
          <label>
            Activo
            <input type="checkbox" checked={form.activo} onChange={(e) => setForm({ ...form, activo: e.target.checked })} />
          </label>
        )}
        <button type="submit">{editandoId === null ? "Crear usuario" : "Guardar cambios"}</button>
        {editandoId !== null && <button type="button" className="secundario" onClick={cancelar}>Cancelar</button>}
      </form>

      {error && <p className="error" role="alert">{error}</p>}

      <table>
        <thead>
          <tr><th>Nombre</th><th>Correo</th><th>Roles</th><th>Estado</th><th>Acciones</th></tr>
        </thead>
        <tbody>
          {usuarios.map((u) => (
            <tr key={u.id}>
              <td>{u.nombre}</td>
              <td>{u.correo}</td>
              <td>{u.roles.map(etiquetaRol).join(", ")}</td>
              <td>
                {u.activo ? "Activo" : "Inactivo"}
                {u.debe_cambiar_password && " · contraseña temporal pendiente"}
              </td>
              <td className="acciones">
                <button
                  className="secundario"
                  onClick={() => {
                    setError("");
                    setEditandoId(u.id);
                    setForm({ nombre: u.nombre, correo: u.correo, roles: u.roles, activo: u.activo });
                  }}
                >
                  Editar
                </button>
                <button className="secundario" onClick={() => restablecer(u)}>Restablecer contraseña</button>
                {u.id === yo?.id && <em>(tú)</em>}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
