import { FormEvent, useCallback, useEffect, useState } from "react";
import { api } from "../../shared/api/client";
import { ESTADOS_LLAMADA, fechaLocal, Llamada, MensajeWA, Seguimiento } from "./api";

interface Generado { id: number; texto: string; enlace: string; tutor: { id: number; nombre: string; telefono: string } }

export const InsigniaLlamada = ({ estado }: { estado: string }) => (
  <span className={`badge llamada-${estado}`}>{ESTADOS_LLAMADA[estado] ?? estado}</span>
);

/** Solo lectura: lo ven Subdirección y Dirección (sin teléfonos). */
export function HistorialLlamadas({ llamadas, mensajes }: { llamadas: Llamada[]; mensajes: MensajeWA[] }) {
  return (
    <>
      {llamadas.length === 0 ? <p>Sin llamadas registradas.</p> : (
        <table>
          <thead><tr><th>Fecha</th><th>Con</th><th>Resultado</th><th>Atendió</th><th>Registró</th><th>Observaciones</th></tr></thead>
          <tbody>{llamadas.map((l) => (
            <tr key={l.id}>
              <td>{fechaLocal(l.fecha_hora)}</td><td>{l.tutor}{l.parentesco ? ` (${l.parentesco})` : ""}</td>
              <td><InsigniaLlamada estado={l.estado} /></td><td>{l.atendio_nombre ?? "—"}</td>
              <td>{l.realizado_por ?? "—"}</td><td>{l.observaciones ?? "—"}</td>
            </tr>
          ))}</tbody>
        </table>
      )}
      {mensajes.length > 0 && (
        <p><small>Mensajes de WhatsApp: {mensajes.map((m) => `${m.tutor} (${m.enviado_en ? "enviado" : "generado"} ${fechaLocal(m.enviado_en ?? m.generado_en)})`).join(" · ")}</small></p>
      )}
    </>
  );
}

/** Panel de trabajo de Orientación Educativa: llamar, registrar el resultado y enviar el WhatsApp. */
export function SeguimientoLlamadas({ reporteId, alCambiar }: { reporteId: number; alCambiar: () => void }) {
  const [seg, setSeg] = useState<Seguimiento | null>(null);
  const [error, setError] = useState("");
  const [aviso, setAviso] = useState("");
  const [generado, setGenerado] = useState<Generado | null>(null);
  const [f, setF] = useState({ tutor: "", estado: "REALIZADA", atendio: "", observaciones: "", fecha: "" });

  const cargar = useCallback(async () => {
    try {
      const s = await api<Seguimiento>(`/reportes/${reporteId}/llamadas`);
      setSeg(s);
      setF((prev) => ({ ...prev, tutor: prev.tutor || String(s.tutores.find((t) => t.es_principal)?.id ?? s.tutores[0]?.id ?? "") }));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al cargar el seguimiento");
    }
  }, [reporteId]);
  useEffect(() => { cargar(); }, [cargar]);

  async function registrar(e: FormEvent) {
    e.preventDefault();
    setError(""); setAviso("");
    const cuerpo: Record<string, unknown> = { estado: f.estado, tutor_legal_id: Number(f.tutor) };
    if (f.estado === "ATENDIDA") cuerpo.atendio_nombre = f.atendio;
    if (f.observaciones.trim()) cuerpo.observaciones = f.observaciones;
    if (f.fecha) cuerpo.fecha_hora = f.fecha;
    try {
      setSeg(await api<Seguimiento>(`/reportes/${reporteId}/llamadas`, { method: "POST", body: JSON.stringify(cuerpo) }));
      setF({ ...f, atendio: "", observaciones: "", fecha: "" });
      setAviso("Llamada registrada.");
      alCambiar();
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo registrar la llamada");
    }
  }

  async function generar(tutorId: number) {
    setError(""); setAviso("");
    try {
      setGenerado(await api<Generado>(`/reportes/${reporteId}/whatsapp`, { method: "POST", body: JSON.stringify({ tutor_legal_id: tutorId }) }));
      await cargar();
      alCambiar();
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo generar el mensaje");
    }
  }

  async function marcarEnviado() {
    if (!generado) return;
    try {
      await api(`/mensajes-whatsapp/${generado.id}/enviado`, { method: "POST" });
      setGenerado(null);
      setAviso("Mensaje marcado como enviado.");
      await cargar();
      alCambiar();
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo marcar el mensaje");
    }
  }

  if (!seg) return <div className="tarjeta">{error ? <p className="error" role="alert">{error}</p> : <p>Cargando seguimiento…</p>}</div>;

  return (
    <div className="tarjeta">
      <h2>Seguimiento con padres o tutores <InsigniaLlamada estado={seg.estado_llamada} /></h2>
      {aviso && <p className="ok" role="status">{aviso}</p>}
      {error && <p className="error" role="alert">{error}</p>}

      <table>
        <thead><tr><th>Padre o tutor</th><th>Parentesco</th><th>Teléfono</th><th /></tr></thead>
        <tbody>{seg.tutores.map((t) => (
          <tr key={t.id}>
            <td>{t.nombre} {t.es_principal && <span className="etiqueta">Principal</span>}</td>
            <td>{t.parentesco ?? "—"}</td>
            <td><a href={`tel:${t.telefono}`}>{t.telefono}</a></td>
            <td><button className="secundario" onClick={() => generar(t.id)}>Mensaje de WhatsApp</button></td>
          </tr>
        ))}</tbody>
      </table>

      {generado && (
        <div style={{ marginTop: "1rem" }}>
          <p><strong>Mensaje para {generado.tutor.nombre}</strong> (revísalo antes de enviarlo):</p>
          <div className="mensaje-wa">{generado.texto}</div>
          <div className="fila-botones" style={{ marginTop: "0.6rem" }}>
            <a className="boton" href={generado.enlace} target="_blank" rel="noopener noreferrer">Abrir en WhatsApp</a>
            <button className="secundario" onClick={() => navigator.clipboard?.writeText(generado.texto)}>Copiar texto</button>
            <button onClick={marcarEnviado}>Ya lo envié</button>
          </div>
        </div>
      )}

      <h2 style={{ marginTop: "1.2rem" }}>Registrar resultado de una llamada</h2>
      <form className="formulario" onSubmit={registrar}>
        <label>Se llamó a
          <select value={f.tutor} onChange={(e) => setF({ ...f, tutor: e.target.value })} required>
            {seg.tutores.map((t) => <option key={t.id} value={t.id}>{t.nombre}{t.parentesco ? ` (${t.parentesco})` : ""}</option>)}
          </select>
        </label>
        <label>Resultado
          <select value={f.estado} onChange={(e) => setF({ ...f, estado: e.target.value })}>
            {["REALIZADA", "NO_CONTESTO", "ATENDIDA"].map((s) => <option key={s} value={s}>{ESTADOS_LLAMADA[s]}</option>)}
          </select>
        </label>
        {f.estado === "ATENDIDA" && (
          <label>¿Quién atendió?
            <input required maxLength={120} value={f.atendio} onChange={(e) => setF({ ...f, atendio: e.target.value })} />
          </label>
        )}
        <label>Fecha y hora (vacío = ahora)
          <input type="datetime-local" value={f.fecha} onChange={(e) => setF({ ...f, fecha: e.target.value })} />
        </label>
        <label style={{ flex: "1 1 260px" }}>Observaciones
          <input maxLength={500} value={f.observaciones} onChange={(e) => setF({ ...f, observaciones: e.target.value })} />
        </label>
        <button type="submit">Registrar</button>
      </form>
      <p><small>Si no contestaron, registra “No contestó” y vuelve a intentar más tarde: cada intento queda guardado. Para concluir el reporte se requiere al menos una llamada Realizada o Atendida.</small></p>

      <h2>Historial de llamadas</h2>
      <HistorialLlamadas llamadas={seg.llamadas} mensajes={seg.mensajes} />
    </div>
  );
}
