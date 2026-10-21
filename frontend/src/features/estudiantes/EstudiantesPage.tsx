import { FormEvent, useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../../app/AuthContext";
import { api } from "../../shared/api/client";
import { ESTATUS, Grupo } from "./api";

interface Fila { id: number; numero_control: string; nombre_completo: string; telefono: string | null; estatus: string; grupo: string | null; carrera: string | null }

export function EstudiantesPage() {
  const { puede } = useAuth();
  const [filas, setFilas] = useState<Fila[]>([]);
  const [grupos, setGrupos] = useState<Grupo[]>([]);
  const [q, setQ] = useState("");
  const [grupoId, setGrupoId] = useState("");
  const [estatus, setEstatus] = useState("");
  const [error, setError] = useState("");
  const [cargando, setCargando] = useState(false);

  const buscar = useCallback(async () => {
    setCargando(true);
    setError("");
    const params = new URLSearchParams();
    if (q.trim()) params.set("q", q.trim());
    if (grupoId) params.set("grupo_id", grupoId);
    if (estatus) params.set("estatus", estatus);
    try {
      setFilas(await api<Fila[]>(`/estudiantes?${params}`));
    } catch (e) {
      setFilas([]);
      setError(e instanceof Error ? e.message : "Error al cargar");
    } finally {
      setCargando(false);
    }
  }, [q, grupoId, estatus]);

  useEffect(() => {
    api<Grupo[]>("/grupos").then(setGrupos).catch(() => undefined);
    buscar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function enviar(e: FormEvent) {
    e.preventDefault();
    buscar();
  }

  return (
    <section>
      <h1>Estudiantes</h1>
      <form className="formulario" onSubmit={enviar}>
        <label>
          Buscar (control, apellidos o nombre)
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Ej. pérez 2430" />
        </label>
        <label>
          Grupo
          <select value={grupoId} onChange={(e) => setGrupoId(e.target.value)}>
            <option value="">Todos</option>
            {grupos.map((g) => <option key={g.id} value={g.id}>{g.clave}</option>)}
          </select>
        </label>
        <label>
          Estatus
          <select value={estatus} onChange={(e) => setEstatus(e.target.value)}>
            <option value="">Todos</option>
            {ESTATUS.map((s) => <option key={s}>{s}</option>)}
          </select>
        </label>
        <button type="submit">Buscar</button>
      </form>
      {puede("GESTIONAR_ESTUDIANTES") && (
        <div className="fila-botones"><Link className="boton" to="/estudiantes/nuevo">Nuevo estudiante</Link></div>
      )}
      {error && <p className="error" role="alert">{error}</p>}
      <table>
        <thead><tr><th>Control</th><th>Nombre</th><th>Grupo</th><th>Carrera</th><th>Teléfono</th><th>Estatus</th><th /></tr></thead>
        <tbody>
          {filas.map((f) => (
            <tr key={f.id}>
              <td>{f.numero_control}</td><td>{f.nombre_completo}</td><td>{f.grupo ?? "—"}</td>
              <td>{f.carrera ?? "—"}</td><td>{f.telefono ?? "—"}</td><td><span className="etiqueta">{f.estatus}</span></td>
              <td><Link to={`/estudiantes/${f.id}`}>Ver</Link></td>
            </tr>
          ))}
          {!cargando && filas.length === 0 && <tr><td colSpan={7}>Sin resultados.</td></tr>}
        </tbody>
      </table>
      {filas.length >= 200 && <p>Se muestran los primeros 200. Afina la búsqueda para ver otros.</p>}
    </section>
  );
}
