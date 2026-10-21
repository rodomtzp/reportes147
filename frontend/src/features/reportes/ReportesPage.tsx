import { FormEvent, useCallback, useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api } from "../../shared/api/client";
import { PanelExportar } from "../exportaciones/PanelExportar";
import { Grupo } from "../estudiantes/api";
import { InsigniaLlamada } from "./SeguimientoLlamadas";
import { ESTADOS, etiquetaEstado, etiquetaGravedad, fechaLocal, GRAVEDADES, ReporteFila } from "./api";

export function ReportesPage() {
  const [params] = useSearchParams();
  const estudianteId = params.get("estudiante_id");
  const [filas, setFilas] = useState<ReporteFila[]>([]);
  const [grupos, setGrupos] = useState<Grupo[]>([]);
  const [f, setF] = useState({ q: "", estado: "", gravedad: "", grupo_id: "", desde: "", hasta: "", cancelados: false, sinLlamada: params.get("sin_llamada") === "true" });
  const [error, setError] = useState("");

  const buscar = useCallback(async () => {
    setError("");
    const p = new URLSearchParams();
    if (estudianteId) p.set("estudiante_id", estudianteId);
    if (f.q.trim()) p.set("q", f.q.trim());
    (["estado", "gravedad", "grupo_id", "desde", "hasta"] as const).forEach((k) => f[k] && p.set(k, f[k]));
    if (f.cancelados) p.set("incluir_cancelados", "true");
    if (f.sinLlamada) p.set("sin_llamada_efectiva", "true");
    try {
      setFilas(await api<ReporteFila[]>(`/reportes?${p}`));
    } catch (e) {
      setFilas([]);
      setError(e instanceof Error ? e.message : "Error al cargar");
    }
  }, [f, estudianteId]);

  useEffect(() => {
    api<Grupo[]>("/grupos").then(setGrupos).catch(() => undefined);
    buscar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [estudianteId]);

  const enviar = (e: FormEvent) => { e.preventDefault(); buscar(); };

  return (
    <section>
      <h1>Reportes{estudianteId && filas[0] ? ` de ${filas[0].estudiante}` : ""}</h1>
      <form className="formulario" onSubmit={enviar}>
        <label>Folio o estudiante<input value={f.q} onChange={(e) => setF({ ...f, q: e.target.value })} placeholder="RPT-2026-0001 o nombre" /></label>
        <label>Estado
          <select value={f.estado} onChange={(e) => setF({ ...f, estado: e.target.value })}>
            <option value="">Todos</option>{ESTADOS.map((s) => <option key={s.valor} value={s.valor}>{s.etiqueta}</option>)}
          </select>
        </label>
        <label>Gravedad
          <select value={f.gravedad} onChange={(e) => setF({ ...f, gravedad: e.target.value })}>
            <option value="">Todas</option>{GRAVEDADES.map((g) => <option key={g.valor} value={g.valor}>{g.etiqueta}</option>)}
          </select>
        </label>
        <label>Grupo
          <select value={f.grupo_id} onChange={(e) => setF({ ...f, grupo_id: e.target.value })}>
            <option value="">Todos</option>{grupos.map((g) => <option key={g.id} value={g.id}>{g.clave}</option>)}
          </select>
        </label>
        <label>Desde<input type="date" value={f.desde} onChange={(e) => setF({ ...f, desde: e.target.value })} /></label>
        <label>Hasta<input type="date" value={f.hasta} onChange={(e) => setF({ ...f, hasta: e.target.value })} /></label>
        <label>Cancelados<input type="checkbox" checked={f.cancelados} onChange={(e) => setF({ ...f, cancelados: e.target.checked })} /></label>
        <label>Sin llamada realizada<input type="checkbox" checked={f.sinLlamada} onChange={(e) => setF({ ...f, sinLlamada: e.target.checked })} /></label>
        <button type="submit">Filtrar</button>
      </form>
      <PanelExportar estudianteId={estudianteId} grupoId={f.grupo_id} desde={f.desde} hasta={f.hasta} />
      {error && <p className="error" role="alert">{error}</p>}
      <table>
        <thead><tr><th>Folio</th><th>Fecha</th><th>Estudiante</th><th>Grupo</th><th>Incidencia</th><th>Gravedad</th><th>Estado</th><th>Llamada</th><th /></tr></thead>
        <tbody>
          {filas.map((r) => (
            <tr key={r.id}>
              <td>{r.folio}</td><td>{fechaLocal(r.fecha_hora_incidente)}</td>
              <td>{r.estudiante}<br /><small>{r.numero_control}</small></td><td>{r.grupo ?? "—"}</td>
              <td>{r.tipo_incidencia}{r.descripcion_otro ? `: ${r.descripcion_otro}` : ""}</td>
              <td><span className={`badge ${r.gravedad}`}>{etiquetaGravedad(r.gravedad)}</span></td>
              <td>{r.cancelado ? <span className="badge cancelado">Cancelado</span> : etiquetaEstado(r.estado)}</td>
              <td>{r.cancelado ? "—" : <InsigniaLlamada estado={r.estado_llamada} />}</td>
              <td><Link to={`/reportes/${r.id}`}>Ver</Link></td>
            </tr>
          ))}
          {filas.length === 0 && <tr><td colSpan={9}>Sin reportes.</td></tr>}
        </tbody>
      </table>
    </section>
  );
}
