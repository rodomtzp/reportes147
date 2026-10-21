import { FormEvent, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../../shared/api/client";
import { GRAVEDADES, TipoIncidencia } from "./api";

interface Encontrado { id: number; numero_control: string; nombre_completo: string; grupo: string | null }
interface Creado { id: number; folio: string; estudiante: string; numero_control: string }

export function NuevoReportePage() {
  const [q, setQ] = useState("");
  const [encontrados, setEncontrados] = useState<Encontrado[]>([]);
  const [elegidos, setElegidos] = useState<Encontrado[]>([]);
  const [tipos, setTipos] = useState<TipoIncidencia[]>([]);
  const [tipoId, setTipoId] = useState("");
  const [otro, setOtro] = useState("");
  const [gravedad, setGravedad] = useState("LEVE");
  const [fecha, setFecha] = useState("");
  const [descripcion, setDescripcion] = useState("");
  const [error, setError] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [creados, setCreados] = useState<Creado[] | null>(null);
  const [mensajeArchivo, setMensajeArchivo] = useState("");
  const archivo = useRef<HTMLInputElement>(null);

  useEffect(() => {
    api<TipoIncidencia[]>("/tipos-incidencia?solo_activos=true").then(setTipos).catch(() => undefined);
  }, []);

  // Búsqueda con pequeña espera para no consultar en cada tecla.
  useEffect(() => {
    if (q.trim().length < 2) return setEncontrados([]);
    const t = setTimeout(() => {
      api<Encontrado[]>(`/estudiantes/buscar?q=${encodeURIComponent(q.trim())}`).then(setEncontrados).catch(() => setEncontrados([]));
    }, 300);
    return () => clearTimeout(t);
  }, [q]);

  const tipo = tipos.find((t) => String(t.id) === tipoId);

  function agregar(e: Encontrado) {
    if (!elegidos.some((x) => x.id === e.id)) setElegidos([...elegidos, e]);
    setQ("");
    setEncontrados([]);
  }

  async function enviar(ev: FormEvent) {
    ev.preventDefault();
    setError("");
    if (elegidos.length === 0) return setError("Selecciona al menos un estudiante.");
    setEnviando(true);
    try {
      const cuerpo: Record<string, unknown> = {
        estudiante_ids: elegidos.map((e) => e.id), tipo_incidencia_id: Number(tipoId), gravedad, descripcion,
      };
      if (tipo?.es_otro) cuerpo.descripcion_otro = otro;
      if (fecha) cuerpo.fecha_hora_incidente = fecha;
      setCreados(await api<Creado[]>("/reportes", { method: "POST", body: JSON.stringify(cuerpo) }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo crear el reporte");
    } finally {
      setEnviando(false);
    }
  }

  async function subirEvidencia() {
    const f = archivo.current?.files?.[0];
    if (!f || !creados) return;
    setMensajeArchivo("");
    try {
      const datos = new FormData();
      datos.append("archivo", f);
      datos.append("aplicar_a_incidente", "true");
      await api(`/reportes/${creados[0].id}/adjuntos`, { method: "POST", body: datos });
      setMensajeArchivo(`Evidencia "${f.name}" agregada.`);
      if (archivo.current) archivo.current.value = "";
    } catch (err) {
      setMensajeArchivo(err instanceof Error ? err.message : "No se pudo subir el archivo");
    }
  }

  function reiniciar() {
    setCreados(null); setElegidos([]); setDescripcion(""); setOtro(""); setFecha(""); setGravedad("LEVE"); setMensajeArchivo("");
  }

  if (creados) {
    return (
      <section>
        <h1>Reporte registrado</h1>
        <div className="tarjeta">
          <p className="ok" role="status">Se generó {creados.length === 1 ? "el siguiente reporte" : `${creados.length} reportes (uno por estudiante)`} y se turnó a Orientación Educativa:</p>
          <ul>{creados.map((c) => <li key={c.id}><strong>{c.folio}</strong> – {c.estudiante} ({c.numero_control})</li>)}</ul>
        </div>
        <div className="tarjeta">
          <h2>Evidencias (opcional)</h2>
          <p>Imágenes JPG, PNG o WEBP, o PDF, de hasta 5 MB. {creados.length > 1 && "Se agregan a todos los reportes de este incidente."}</p>
          <div className="fila-botones">
            <input ref={archivo} type="file" accept=".jpg,.jpeg,.png,.webp,.pdf" />
            <button type="button" onClick={subirEvidencia}>Subir</button>
          </div>
          {mensajeArchivo && <p role="status">{mensajeArchivo}</p>}
        </div>
        <div className="fila-botones"><button onClick={reiniciar}>Crear otro reporte</button><Link to="/">Terminar</Link></div>
      </section>
    );
  }

  return (
    <section>
      <h1>Nuevo reporte</h1>
      <form onSubmit={enviar}>
        <div className="tarjeta">
          <h2>Estudiante(s) involucrado(s)</h2>
          <input placeholder="Busca por número de control, apellidos o nombre" value={q} onChange={(e) => setQ(e.target.value)} className="ancho" />
          {encontrados.length > 0 && (
            <ul>{encontrados.map((e) => (
              <li key={e.id}>{e.numero_control} – {e.nombre_completo} ({e.grupo ?? "sin grupo"}){" "}
                <button type="button" className="secundario" onClick={() => agregar(e)}>Agregar</button></li>
            ))}</ul>
          )}
          <div className="chips">
            {elegidos.map((e) => (
              <span className="chip" key={e.id}>{e.nombre_completo} · {e.grupo ?? "—"}
                <button type="button" aria-label={`Quitar ${e.nombre_completo}`} onClick={() => setElegidos(elegidos.filter((x) => x.id !== e.id))}>×</button></span>
            ))}
          </div>
          {elegidos.length > 1 && <p>Se creará un reporte por estudiante, ligados al mismo incidente.</p>}
        </div>

        <div className="tarjeta">
          <h2>Incidente</h2>
          <div className="formulario sin-marco">
            <label>Tipo de incidencia
              <select required value={tipoId} onChange={(e) => setTipoId(e.target.value)}>
                <option value="">— Selecciona —</option>
                {tipos.map((t) => <option key={t.id} value={t.id}>{t.nombre}</option>)}
              </select>
            </label>
            {tipo?.es_otro && (
              <label>Especifica el tipo
                <input required maxLength={200} value={otro} onChange={(e) => setOtro(e.target.value)} />
              </label>
            )}
            <label>Gravedad
              <select value={gravedad} onChange={(e) => setGravedad(e.target.value)}>
                {GRAVEDADES.map((g) => <option key={g.valor} value={g.valor}>{g.etiqueta}</option>)}
              </select>
            </label>
            <label>Fecha y hora (vacío = ahora)
              <input type="datetime-local" value={fecha} onChange={(e) => setFecha(e.target.value)} />
            </label>
          </div>
          {(gravedad === "GRAVE" || gravedad === "MUY_GRAVE") && (
            <p className="aviso">Un reporte Grave o Muy grave alerta de inmediato a Subdirección.</p>
          )}
          <label>Descripción de los hechos (mínimo 10 caracteres)
            <textarea required minLength={10} maxLength={2000} rows={5} value={descripcion} onChange={(e) => setDescripcion(e.target.value)} />
          </label>
        </div>

        {error && <p className="error" role="alert">{error}</p>}
        <button type="submit" disabled={enviando}>{enviando ? "Guardando…" : "Generar reporte"}</button>
      </form>
    </section>
  );
}
