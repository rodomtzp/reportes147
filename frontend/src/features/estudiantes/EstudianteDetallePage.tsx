import { FormEvent, useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useAuth } from "../../app/AuthContext";
import { api } from "../../shared/api/client";
import { Detalle, ESTATUS, Grupo, Tutor } from "./api";

const CAMPOS_EDITABLES: [keyof Detalle, string][] = [
  ["primer_apellido", "Primer apellido"], ["segundo_apellido", "Segundo apellido"], ["nombres", "Nombre(s)"],
  ["telefono", "Teléfono"], ["correo", "Correo"], ["generacion", "Generación"],
  ["calle", "Calle"], ["numero", "Número"], ["colonia", "Colonia"], ["ciudad", "Ciudad"],
];
const TUTOR_VACIO = { nombre: "", parentesco: "", telefono: "", correo: "" };

export function EstudianteDetallePage() {
  const { id } = useParams();
  const { puede, usuario } = useAuth();
  const puedeEditar = puede("GESTIONAR_ESTUDIANTES");
  const [d, setD] = useState<Detalle | null>(null);
  const [grupos, setGrupos] = useState<Grupo[]>([]);
  const [edicion, setEdicion] = useState<Record<string, string> | null>(null);
  const [grupoNuevo, setGrupoNuevo] = useState("");
  const [tutor, setTutor] = useState(TUTOR_VACIO);
  const [error, setError] = useState("");

  const cargar = useCallback(async () => {
    try {
      setD(await api<Detalle>(`/estudiantes/${id}`));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al cargar");
    }
  }, [id]);

  useEffect(() => {
    cargar();
    if (puedeEditar) api<Grupo[]>("/grupos?solo_activos=true").then(setGrupos).catch(() => undefined);
  }, [cargar, puedeEditar]);

  async function accion(fn: () => Promise<unknown>) {
    setError("");
    try {
      await fn();
      await cargar();
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo completar la acción");
    }
  }

  function iniciarEdicion(actual: Detalle) {
    const inicial: Record<string, string> = { estatus: actual.estatus };
    CAMPOS_EDITABLES.forEach(([k]) => {
      inicial[k as string] = (actual[k] as string | null) ?? "";
    });
    setEdicion(inicial);
  }

  const guardarEdicion = (e: FormEvent) => {
    e.preventDefault();
    accion(async () => {
      await api(`/estudiantes/${id}`, { method: "PATCH", body: JSON.stringify(edicion) });
      setEdicion(null);
    });
  };
  const cambiarGrupo = () =>
    accion(async () => {
      await api(`/estudiantes/${id}/grupo`, { method: "POST", body: JSON.stringify({ grupo_id: Number(grupoNuevo) }) });
      setGrupoNuevo("");
    });
  const agregarTutor = (e: FormEvent) => {
    e.preventDefault();
    const cuerpo = Object.fromEntries(Object.entries(tutor).filter(([, v]) => v.trim() !== ""));
    accion(async () => {
      await api(`/estudiantes/${id}/tutores-legales`, { method: "POST", body: JSON.stringify(cuerpo) });
      setTutor(TUTOR_VACIO);
    });
  };
  const hacerPrincipal = (t: Tutor) =>
    accion(() => api(`/tutores-legales/${t.id}`, { method: "PATCH", body: JSON.stringify({ es_principal: true }) }));
  const quitarTutor = (t: Tutor) =>
    window.confirm(`¿Quitar a ${t.nombre}?`) && accion(() => api(`/tutores-legales/${t.id}`, { method: "DELETE" }));

  if (!d) return <section>{error ? <p className="error" role="alert">{error}</p> : <p>Cargando…</p>}<Link to="/estudiantes">← Volver</Link></section>;

  const dato = (etiqueta: string, valor: string | null) => (<><dt>{etiqueta}</dt><dd>{valor || "—"}</dd></>);

  return (
    <section>
      <p><Link to="/estudiantes">← Estudiantes</Link></p>
      <h1>{d.nombre_completo} <span className="etiqueta">{d.estatus}</span></h1>
      {(puede("VER_TODOS_LOS_REPORTES") || (usuario?.grupos_tutelados.length ?? 0) > 0) && (
        <p><Link to={`/reportes?estudiante_id=${d.id}`}>Ver reportes de este estudiante</Link>{puede("VER_TODOS_LOS_REPORTES") && <> · <Link to={`/estudiantes/${d.id}/expediente`}>Expediente disciplinario</Link></>}</p>
      )}
      {error && <p className="error" role="alert">{error}</p>}

      <div className="tarjeta">
        <h2>Datos del estudiante</h2>
        {edicion === null ? (
          <>
            <dl className="datos">
              {dato("Número de control", d.numero_control)}{dato("Generación", d.generacion)}
              {dato("Grupo actual", d.grupo_actual)}{dato("Carrera", d.carrera_actual)}
              {dato("Teléfono", d.telefono)}{dato("Correo", d.correo)}
              {dato("Dirección", [d.calle, d.numero, d.colonia, d.ciudad].filter(Boolean).join(", "))}
            </dl>
            {puedeEditar && (
              <button className="secundario" onClick={() => iniciarEdicion(d)}>Editar datos</button>
            )}
          </>
        ) : (
          <form className="formulario sin-marco" onSubmit={guardarEdicion}>
            {CAMPOS_EDITABLES.map(([k, etiqueta]) => (
              <label key={k}>{etiqueta}
                <input value={edicion[k] ?? ""} onChange={(e) => setEdicion({ ...edicion, [k]: e.target.value })} />
              </label>
            ))}
            <label>Estatus
              <select value={edicion.estatus} onChange={(e) => setEdicion({ ...edicion, estatus: e.target.value })}>
                {ESTATUS.map((s) => <option key={s}>{s}</option>)}
              </select>
            </label>
            <button type="submit">Guardar</button>
            <button type="button" className="secundario" onClick={() => setEdicion(null)}>Cancelar</button>
          </form>
        )}
      </div>

      <div className="tarjeta">
        <h2>Padres o tutores legales</h2>
        <table>
          <thead><tr><th>Nombre</th><th>Parentesco</th><th>Teléfono</th><th>Correo</th>{puedeEditar && <th>Acciones</th>}</tr></thead>
          <tbody>
            {d.tutores_legales.map((t) => (
              <tr key={t.id}>
                <td>{t.nombre} {t.es_principal && <span className="etiqueta">Principal</span>}</td>
                <td>{t.parentesco ?? "—"}</td><td>{t.telefono}</td><td>{t.correo ?? "—"}</td>
                {puedeEditar && (
                  <td className="acciones">
                    {!t.es_principal && <button className="secundario" onClick={() => hacerPrincipal(t)}>Hacer principal</button>}
                    <button className="peligro" onClick={() => quitarTutor(t)}>Quitar</button>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
        {puedeEditar && (
          <form className="formulario separado" onSubmit={agregarTutor}>
            <label>Nombre<input required value={tutor.nombre} onChange={(e) => setTutor({ ...tutor, nombre: e.target.value })} /></label>
            <label>Parentesco<input value={tutor.parentesco} onChange={(e) => setTutor({ ...tutor, parentesco: e.target.value })} /></label>
            <label>Teléfono<input required type="tel" value={tutor.telefono} onChange={(e) => setTutor({ ...tutor, telefono: e.target.value })} /></label>
            <label>Correo<input type="email" value={tutor.correo} onChange={(e) => setTutor({ ...tutor, correo: e.target.value })} /></label>
            <button type="submit">Agregar tutor</button>
          </form>
        )}
      </div>

      <div className="tarjeta">
        <h2>Historial de grupos</h2>
        <table>
          <thead><tr><th>Periodo</th><th>Grupo</th><th>Semestre</th><th>Carrera</th></tr></thead>
          <tbody>
            {d.historial.map((h) => <tr key={h.periodo}><td>{h.periodo}</td><td>{h.grupo}</td><td>{h.semestre}</td><td>{h.carrera}</td></tr>)}
            {d.historial.length === 0 && <tr><td colSpan={4}>Sin inscripciones.</td></tr>}
          </tbody>
        </table>
        {puedeEditar && d.estatus === "ACTIVO" && (
          <div className="fila-botones" style={{ marginTop: "1rem" }}>
            <label>Corregir grupo del periodo vigente:{" "}
              <select value={grupoNuevo} onChange={(e) => setGrupoNuevo(e.target.value)}>
                <option value="">— Selecciona —</option>
                {grupos.map((g) => <option key={g.id} value={g.id}>{g.clave}</option>)}
              </select>
            </label>
            <button disabled={!grupoNuevo} onClick={cambiarGrupo}>Cambiar grupo</button>
          </div>
        )}
      </div>
    </section>
  );
}
