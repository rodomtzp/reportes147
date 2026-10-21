import { useEffect, useState } from "react";
import { api } from "../../shared/api/client";

interface Periodo { id: number; nombre: string; vigente: boolean; fecha_inicio: string }
interface Encontrado { id: number; numero_control: string; nombre_completo: string; grupo: string | null }
interface Movimiento { estudiante_id: number; numero_control: string; nombre: string; grupo_origen: string; grupo_destino: string | null; accion: string }
interface Resumen { ejecutado: boolean; grupos_faltantes: string[]; omitidos_ya_inscritos: number; conteo: Record<string, number>; movimientos: Movimiento[] }
interface Excepcion { estudiante: Encontrado; accion: "REPETIR" | "BAJA" }

const ETIQUETA: Record<string, string> = { AVANZA: "Avanzan", REPITE: "Repiten", EGRESA: "Egresan", BAJA: "Bajas" };

export function AvanceSemestrePage() {
  const [periodos, setPeriodos] = useState<Periodo[]>([]);
  const [origen, setOrigen] = useState("");
  const [destino, setDestino] = useState("");
  const [q, setQ] = useState("");
  const [encontrados, setEncontrados] = useState<Encontrado[]>([]);
  const [excepciones, setExcepciones] = useState<Excepcion[]>([]);
  const [resumen, setResumen] = useState<Resumen | null>(null);
  const [error, setError] = useState("");
  const [trabajando, setTrabajando] = useState(false);

  useEffect(() => {
    api<Periodo[]>("/periodos").then((p) => {
      setPeriodos(p);
      const vigente = p.find((x) => x.vigente);
      if (vigente) setOrigen(String(vigente.id));
    });
  }, []);

  const invalidar = () => setResumen(null); // cualquier cambio exige recalcular la vista previa

  async function buscar() {
    setError("");
    try {
      setEncontrados(await api<Encontrado[]>(`/estudiantes?q=${encodeURIComponent(q)}&estatus=ACTIVO&limite=8`));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error en la búsqueda");
    }
  }

  function agregar(e: Encontrado) {
    if (!excepciones.some((x) => x.estudiante.id === e.id)) setExcepciones([...excepciones, { estudiante: e, accion: "REPETIR" }]);
    invalidar();
  }

  async function calcular(simular: boolean) {
    setError("");
    setTrabajando(true);
    try {
      setResumen(await api<Resumen>("/estudiantes/avance-semestre", {
        method: "POST",
        body: JSON.stringify({
          periodo_origen_id: Number(origen), periodo_destino_id: Number(destino), simular,
          excepciones: excepciones.map((x) => ({ estudiante_id: x.estudiante.id, accion: x.accion })),
        }),
      }));
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo procesar");
    } finally {
      setTrabajando(false);
    }
  }

  async function ejecutar() {
    if (!window.confirm("Se inscribirá a los estudiantes en el nuevo periodo. ¿Continuar?")) return;
    await calcular(false);
  }

  const listo = origen && destino && origen !== destino;
  const puedeEjecutar = resumen && !resumen.ejecutado && resumen.grupos_faltantes.length === 0 && resumen.movimientos.length > 0;

  return (
    <section>
      <h1>Avance de semestre</h1>
      <div className="tarjeta">
        <p>
          Al cerrar el periodo, cada estudiante activo pasa al grupo del siguiente semestre conservando la letra (1G → 2G).
          Los de sexto semestre egresan. Marca aquí las <strong>excepciones</strong> (repetidores y bajas) y revisa la vista previa antes de ejecutar.
          Después, marca el nuevo periodo como <strong>vigente</strong> en la sección Periodos.
        </p>
        <div className="formulario sin-marco">
          <label>Periodo que termina
            <select value={origen} onChange={(e) => { setOrigen(e.target.value); invalidar(); }}>
              <option value="">— Selecciona —</option>
              {periodos.map((p) => <option key={p.id} value={p.id}>{p.nombre}{p.vigente ? " (vigente)" : ""}</option>)}
            </select>
          </label>
          <label>Periodo nuevo
            <select value={destino} onChange={(e) => { setDestino(e.target.value); invalidar(); }}>
              <option value="">— Selecciona —</option>
              {periodos.map((p) => <option key={p.id} value={p.id}>{p.nombre}</option>)}
            </select>
          </label>
        </div>
      </div>

      <div className="tarjeta">
        <h2>Excepciones</h2>
        <div className="fila-botones">
          <input placeholder="Buscar estudiante (control o nombre)" value={q} onChange={(e) => setQ(e.target.value)} />
          <button className="secundario" onClick={buscar}>Buscar</button>
        </div>
        {encontrados.length > 0 && (
          <ul>{encontrados.map((e) => (
            <li key={e.id}>{e.numero_control} – {e.nombre_completo} ({e.grupo ?? "sin grupo"}){" "}
              <button className="secundario" onClick={() => agregar(e)}>Agregar</button></li>
          ))}</ul>
        )}
        {excepciones.length > 0 && (
          <table>
            <thead><tr><th>Estudiante</th><th>Acción</th><th /></tr></thead>
            <tbody>{excepciones.map((x) => (
              <tr key={x.estudiante.id}>
                <td>{x.estudiante.numero_control} – {x.estudiante.nombre_completo}</td>
                <td>
                  <select value={x.accion} onChange={(e) => { setExcepciones(excepciones.map((y) => y === x ? { ...y, accion: e.target.value as Excepcion["accion"] } : y)); invalidar(); }}>
                    <option value="REPETIR">Repite el semestre</option>
                    <option value="BAJA">Causa baja</option>
                  </select>
                </td>
                <td><button className="peligro" onClick={() => { setExcepciones(excepciones.filter((y) => y !== x)); invalidar(); }}>Quitar</button></td>
              </tr>
            ))}</tbody>
          </table>
        )}
      </div>

      {error && <p className="error" role="alert">{error}</p>}
      <div className="fila-botones">
        <button disabled={!listo || trabajando} onClick={() => calcular(true)}>Calcular vista previa</button>
        <button disabled={!puedeEjecutar || trabajando} onClick={ejecutar}>Ejecutar avance</button>
      </div>

      {resumen && (
        <div className="tarjeta">
          <h2>{resumen.ejecutado ? "Avance ejecutado" : "Vista previa"}</h2>
          {resumen.ejecutado && <p className="ok" role="status">Listo. Recuerda marcar el nuevo periodo como vigente en Periodos.</p>}
          {resumen.grupos_faltantes.length > 0 && (
            <p className="error" role="alert">Faltan grupos activos para el siguiente semestre: {resumen.grupos_faltantes.join(", ")}. Créalos en Grupos y vuelve a calcular.</p>
          )}
          <p>
            {Object.entries(resumen.conteo).map(([k, v]) => `${ETIQUETA[k] ?? k}: ${v}`).join(" · ") || "Sin movimientos."}
            {resumen.omitidos_ya_inscritos > 0 && ` · Ya inscritos en el periodo nuevo: ${resumen.omitidos_ya_inscritos}`}
          </p>
          <table>
            <thead><tr><th>Control</th><th>Nombre</th><th>De</th><th>A</th><th>Resultado</th></tr></thead>
            <tbody>{resumen.movimientos.map((m) => (
              <tr key={m.estudiante_id}>
                <td>{m.numero_control}</td><td>{m.nombre}</td><td>{m.grupo_origen}</td>
                <td>{m.grupo_destino ?? "—"}</td><td>{ETIQUETA[m.accion] ?? m.accion}</td>
              </tr>
            ))}</tbody>
          </table>
        </div>
      )}
    </section>
  );
}
