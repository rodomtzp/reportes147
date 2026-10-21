import { FormEvent, useCallback, useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useAuth } from "../../app/AuthContext";
import { api, descargar } from "../../shared/api/client";
import { FormularioSancion, textoSancion } from "../sanciones/FormularioSancion";
import { HistorialLlamadas, InsigniaLlamada, SeguimientoLlamadas } from "./SeguimientoLlamadas";
import { aInputLocal, etiquetaEstado, etiquetaGravedad, fechaLocal, GRAVEDADES, ReporteDetalle, TipoIncidencia } from "./api";

const ETIQUETA_EVENTO: Record<string, string> = {
  CREACION: "Reporte creado", ESTADO: "Cambio de estado", GRAVEDAD: "Cambio de gravedad",
  CORRECCION: "Corrección", CANCELACION: "Cancelación", ADJUNTO: "Evidencia agregada",
};
const kb = (n: number) => (n >= 1048576 ? `${(n / 1048576).toFixed(1)} MB` : `${Math.max(1, Math.round(n / 1024))} KB`);

export function ReporteDetallePage() {
  const { id } = useParams();
  const { usuario, puede } = useAuth();
  const [d, setD] = useState<ReporteDetalle | null>(null);
  const [tipos, setTipos] = useState<TipoIncidencia[]>([]);
  const [error, setError] = useState("");
  const [aviso, setAviso] = useState("");
  const [corrigiendo, setCorrigiendo] = useState(false);
  const [corr, setCorr] = useState({ descripcion: "", tipo: "", otro: "", fecha: "", comentario: "" });
  const [gravedad, setGravedad] = useState("LEVE");
  const [motivoGravedad, setMotivoGravedad] = useState("");
  const [comentarioTurno, setComentarioTurno] = useState("");
  const [motivoCancelacion, setMotivoCancelacion] = useState("");
  const [aTodos, setATodos] = useState(true);
  const archivo = useRef<HTMLInputElement>(null);

  const cargar = useCallback(async () => {
    try {
      setD(await api<ReporteDetalle>(`/reportes/${id}`));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al cargar");
    }
  }, [id]);

  useEffect(() => {
    cargar();
    api<TipoIncidencia[]>("/tipos-incidencia").then(setTipos).catch(() => undefined);
  }, [cargar]);

  async function ejecutar(ruta: string, metodo: string, cuerpo: unknown, exito: string) {
    setError(""); setAviso("");
    try {
      setD(await api<ReporteDetalle>(ruta, { method: metodo, body: JSON.stringify(cuerpo) }));
      setAviso(exito);
      return true;
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo completar la acción");
      return false;
    }
  }

  if (!d) return <section>{error ? <p className="error" role="alert">{error}</p> : <p>Cargando…</p>}<Link to="/reportes">← Reportes</Link></section>;

  const cerrado = d.cancelado || d.estado === "SANCIONADO_CONCLUIDO";
  const esGrave = d.gravedad === "GRAVE" || d.gravedad === "MUY_GRAVE";
  const esAutor = usuario?.nombre === d.creado_por;
  const puedeAdjuntar = !cerrado && (puede("CORREGIR_REPORTE") || (esAutor && d.estado === "EN_REVISION_ORIENTACION"));
  const tipoElegido = tipos.find((t) => String(t.id) === corr.tipo);

  function iniciarCorreccion() {
    if (!d) return;
    setCorr({ descripcion: d.descripcion, tipo: String(d.tipo_incidencia_id), otro: d.descripcion_otro ?? "", fecha: aInputLocal(d.fecha_hora_incidente), comentario: "" });
    setCorrigiendo(true);
  }

  async function guardarCorreccion(e: FormEvent) {
    e.preventDefault();
    if (!d) return;
    const cambios: Record<string, unknown> = {};
    if (corr.descripcion.trim() !== d.descripcion) cambios.descripcion = corr.descripcion;
    if (corr.tipo !== String(d.tipo_incidencia_id)) cambios.tipo_incidencia_id = Number(corr.tipo);
    if (tipoElegido?.es_otro && corr.otro.trim() !== (d.descripcion_otro ?? "")) cambios.descripcion_otro = corr.otro;
    if (corr.fecha !== aInputLocal(d.fecha_hora_incidente)) cambios.fecha_hora_incidente = corr.fecha;
    if (Object.keys(cambios).length === 0) return setError("No hay cambios que guardar.");
    if (corr.comentario.trim()) cambios.comentario = corr.comentario;
    if (await ejecutar(`/reportes/${id}`, "PATCH", cambios, "Cambios guardados.")) setCorrigiendo(false);
  }

  async function subir() {
    const f = archivo.current?.files?.[0];
    if (!f) return setError("Selecciona un archivo.");
    setError(""); setAviso("");
    try {
      const datos = new FormData();
      datos.append("archivo", f);
      if (aTodos && d && d.relacionados.length > 0) datos.append("aplicar_a_incidente", "true");
      await api(`/reportes/${id}/adjuntos`, { method: "POST", body: datos });
      if (archivo.current) archivo.current.value = "";
      setAviso("Evidencia agregada.");
      await cargar();
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo subir el archivo");
    }
  }

  return (
    <section>
      <p><Link to="/reportes">← Reportes</Link></p>
      <h1>
        {d.folio} <span className={`badge ${d.gravedad}`}>{etiquetaGravedad(d.gravedad)}</span>{" "}
        {d.cancelado ? <span className="badge cancelado">Cancelado</span> : <span className="etiqueta">{etiquetaEstado(d.estado)}</span>}{" "}
        Llamada: <InsigniaLlamada estado={d.estado_llamada} />
      </h1>
      {aviso && <p className="ok" role="status">{aviso}</p>}
      {error && <p className="error" role="alert">{error}</p>}

      <div className="tarjeta">
        <dl className="datos">
          <dt>Estudiante</dt><dd>{d.estudiante} ({d.numero_control})</dd>
          <dt>Grupo cuando ocurrió</dt><dd>{d.grupo ?? "—"} · {d.carrera ?? "—"}</dd>
          <dt>Incidencia</dt><dd>{d.tipo_incidencia}{d.descripcion_otro ? `: ${d.descripcion_otro}` : ""}</dd>
          <dt>Fecha del incidente</dt><dd>{fechaLocal(d.fecha_hora_incidente)}</dd>
          <dt>Reportado por</dt><dd>{d.creado_por} · {fechaLocal(d.creado_en)}</dd>
        </dl>
        <h2>Descripción</h2>
        <p style={{ whiteSpace: "pre-wrap" }}>{d.descripcion}</p>
        {d.cancelado && <p className="error"><strong>Cancelado</strong> por {d.cancelado_por ?? "?"} ({fechaLocal(d.cancelado_en)}): {d.motivo_cancelacion}</p>}
        {d.relacionados.length > 0 && (
          <>
            <h2>Otros reportes del mismo incidente</h2>
            <ul>{d.relacionados.map((r) => (
              <li key={r.id}><Link to={`/reportes/${r.id}`}>{r.folio}</Link> – {r.estudiante} ({r.grupo ?? "—"}) <span className={`badge ${r.gravedad}`}>{etiquetaGravedad(r.gravedad)}</span>{r.cancelado && " · cancelado"}</li>
            ))}</ul>
          </>
        )}
      </div>

      <div className="tarjeta">
        <h2>Evidencias</h2>
        {d.adjuntos.length === 0 ? <p>Sin evidencias.</p> : (
          <ul>{d.adjuntos.map((a) => (
            <li key={a.id}>{a.nombre} <small>({kb(a.tamano)})</small>{" "}
              <button className="secundario" onClick={() => descargar(`/reportes/${d.id}/adjuntos/${a.id}`, a.nombre).catch((e) => setError(e.message))}>Descargar</button></li>
          ))}</ul>
        )}
        {puedeAdjuntar && (
          <div className="fila-botones">
            <input ref={archivo} type="file" accept=".jpg,.jpeg,.png,.webp,.pdf" />
            {d.relacionados.length > 0 && (
              <label><input type="checkbox" checked={aTodos} onChange={(e) => setATodos(e.target.checked)} /> Agregar a todos los reportes del incidente</label>
            )}
            <button onClick={subir}>Subir evidencia</button>
          </div>
        )}
      </div>

      {d.sancion && (
        <div className="tarjeta sancion">
          <h2>Sanción</h2>
          <p><strong>{textoSancion(d.sancion)}</strong> · {d.sancion.origen === "ACUMULACION" ? "por acumulación de reportes" : "directa por la magnitud del reporte"}</p>
          <p><small>{d.sancion.aplicada_por} · {fechaLocal(d.sancion.aplicada_en)}{d.sancion.folios.length > 1 ? ` · Cubre: ${d.sancion.folios.join(", ")}` : ""}</small></p>
          {d.sancion.observaciones && <p>“{d.sancion.observaciones}”</p>}
        </div>
      )}

      {d.acumulacion && !d.cancelado && (
        <div className="tarjeta">
          <p className="contador">Ciclo actual del estudiante: <strong>{d.acumulacion.total}</strong> de {d.acumulacion.umbral} reportes
            {d.acumulacion.listo_para_sancion && <span className="badge alerta">Procede sanción</span>}
            {" "}<Link to={`/estudiantes/${d.estudiante_id}/expediente`}>Ver expediente</Link></p>
        </div>
      )}

      {puede("REGISTRAR_LLAMADAS") && !d.cancelado ? (
        <SeguimientoLlamadas reporteId={d.id} alCambiar={cargar} />
      ) : d.llamadas ? (
        <div className="tarjeta"><h2>Llamadas a padres o tutores</h2><HistorialLlamadas llamadas={d.llamadas} mensajes={d.mensajes_whatsapp ?? []} /></div>
      ) : null}

      {!cerrado && (
        <div className="acciones-reporte">
          {puede("CORREGIR_REPORTE") && (
            <div className="tarjeta">
              <h2>Corregir datos</h2>
              {!corrigiendo ? <button className="secundario" onClick={iniciarCorreccion}>Editar reporte</button> : (
                <form onSubmit={guardarCorreccion} className="form-apilado">
                  <label>Tipo de incidencia
                    <select value={corr.tipo} onChange={(e) => setCorr({ ...corr, tipo: e.target.value })}>
                      {tipos.map((t) => <option key={t.id} value={t.id}>{t.nombre}</option>)}
                    </select>
                  </label>
                  {tipoElegido?.es_otro && <label>Especifica el tipo<input value={corr.otro} onChange={(e) => setCorr({ ...corr, otro: e.target.value })} maxLength={200} required /></label>}
                  <label>Fecha y hora<input type="datetime-local" value={corr.fecha} onChange={(e) => setCorr({ ...corr, fecha: e.target.value })} /></label>
                  <label>Descripción<textarea rows={4} minLength={10} maxLength={2000} value={corr.descripcion} onChange={(e) => setCorr({ ...corr, descripcion: e.target.value })} /></label>
                  <label>Comentario (opcional)<input value={corr.comentario} onChange={(e) => setCorr({ ...corr, comentario: e.target.value })} maxLength={500} /></label>
                  <div className="fila-botones"><button type="submit">Guardar</button><button type="button" className="secundario" onClick={() => setCorrigiendo(false)}>Cancelar</button></div>
                </form>
              )}
            </div>
          )}
          {puede("CAMBIAR_GRAVEDAD") && (
            <div className="tarjeta">
              <h2>Cambiar gravedad</h2>
              <form onSubmit={async (e) => { e.preventDefault(); if (await ejecutar(`/reportes/${id}/gravedad`, "POST", { gravedad, motivo: motivoGravedad }, "Gravedad actualizada.")) setMotivoGravedad(""); }} className="form-apilado">
                <select value={gravedad} onChange={(e) => setGravedad(e.target.value)}>
                  {GRAVEDADES.map((g) => <option key={g.valor} value={g.valor}>{g.etiqueta}</option>)}
                </select>
                <input placeholder="Motivo del cambio" required minLength={5} maxLength={500} value={motivoGravedad} onChange={(e) => setMotivoGravedad(e.target.value)} />
                <button type="submit">Cambiar</button>
              </form>
            </div>
          )}
          {puede("TURNAR_A_SUBDIRECCION") && d.estado === "EN_REVISION_ORIENTACION" && (
            <div className="tarjeta">
              <h2>Turnar a Subdirección</h2>
              <input placeholder="Comentario (opcional)" maxLength={500} value={comentarioTurno} onChange={(e) => setComentarioTurno(e.target.value)} className="ancho" />
              <button onClick={() => window.confirm("¿Turnar este reporte a Subdirección?") && ejecutar(`/reportes/${id}/turnar`, "POST", { comentario: comentarioTurno || null }, "Reporte turnado a Subdirección.")}>Turnar</button>
            </div>
          )}
          {puede("APLICAR_SANCIONES") && esGrave && (
            <div className="tarjeta">
              <FormularioSancion
                titulo="Sanción directa" textoBoton="Aplicar sanción y concluir"
                confirmacion="Se aplicará la sanción y el reporte pasará a 'Sancionado / Concluido'. ¿Continuar?"
                alEnviar={async (cuerpo) => {
                  await ejecutar(`/reportes/${id}/sancion`, "POST", cuerpo, "Sanción aplicada.");
                }}
              />
              <p><small>Requiere al menos una llamada Realizada o Atendida. No cierra el ciclo de acumulación del estudiante.</small></p>
            </div>
          )}
          {puede("CANCELAR_REPORTE") && (
            <div className="tarjeta">
              <h2>Cancelar reporte</h2>
              <p><small>Los reportes no se eliminan: se cancelan con motivo y dejan de contar.</small></p>
              <input placeholder="Motivo (mínimo 10 caracteres)" minLength={10} maxLength={500} value={motivoCancelacion} onChange={(e) => setMotivoCancelacion(e.target.value)} className="ancho" />
              <button className="peligro" onClick={() => window.confirm("¿Cancelar este reporte?") && ejecutar(`/reportes/${id}/cancelar`, "POST", { motivo: motivoCancelacion }, "Reporte cancelado.")}>Cancelar reporte</button>
            </div>
          )}
        </div>
      )}

      <div className="tarjeta">
        <h2>Historial</h2>
        {d.historial.map((e) => (
          <div className="linea" key={e.id}>
            <strong>{ETIQUETA_EVENTO[e.tipo] ?? e.tipo}</strong>
            {e.campo && e.tipo !== "ADJUNTO" && ` · ${e.campo}`}
            {(e.valor_anterior || e.valor_nuevo) && e.tipo !== "CREACION" && (
              <> — {e.valor_anterior ? <s>{e.valor_anterior}</s> : "∅"} → {e.valor_nuevo ?? "∅"}</>
            )}
            {e.tipo === "ADJUNTO" && e.valor_nuevo && `: ${e.valor_nuevo}`}
            {e.comentario && <div>“{e.comentario}”</div>}
            <div><small>{e.usuario} · {fechaLocal(e.fecha)}</small></div>
          </div>
        ))}
      </div>
    </section>
  );
}
