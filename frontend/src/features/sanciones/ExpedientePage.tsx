import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useAuth } from "../../app/AuthContext";
import { api } from "../../shared/api/client";
import { CicloExpediente, etiquetaEstado, etiquetaGravedad, Expediente, fechaLocal, SancionInfo } from "../reportes/api";
import { FormularioSancion, textoSancion } from "./FormularioSancion";

function TarjetaSancion({ s }: { s: SancionInfo }) {
  return (
    <div className="tarjeta sancion">
      <strong>{textoSancion(s)}</strong> · {s.origen === "ACUMULACION" ? "por acumulación de reportes" : "directa por la magnitud del reporte"}
      <br /><small>{s.aplicada_por} · {fechaLocal(s.aplicada_en)} · Folios: {s.folios.join(", ")}</small>
      {s.observaciones && <p style={{ margin: "0.4rem 0 0" }}>“{s.observaciones}”</p>}
    </div>
  );
}

function TablaReportes({ ciclo }: { ciclo: CicloExpediente }) {
  return (
    <table>
      <thead><tr><th>Folio</th><th>Fecha</th><th>Incidencia</th><th>Gravedad</th><th>Estado</th><th>Cuenta</th></tr></thead>
      <tbody>
        {ciclo.reportes.map((r) => (
          <tr key={r.id} className={r.cuenta ? "" : "no-cuenta"}>
            <td><Link to={`/reportes/${r.id}`}>{r.folio}</Link></td><td>{fechaLocal(r.fecha_hora_incidente)}</td>
            <td>{r.tipo_incidencia}</td><td><span className={`badge ${r.gravedad}`}>{etiquetaGravedad(r.gravedad)}</span></td>
            <td>{r.cancelado ? "Cancelado" : etiquetaEstado(r.estado)}</td>
            <td>{r.cuenta ? "Sí" : r.cancelado ? "No (cancelado)" : "No (sanción directa)"}</td>
          </tr>
        ))}
        {ciclo.reportes.length === 0 && <tr><td colSpan={6}>Sin reportes.</td></tr>}
      </tbody>
    </table>
  );
}

export function ExpedientePage() {
  const { id } = useParams();
  const { puede } = useAuth();
  const [e, setE] = useState<Expediente | null>(null);
  const [error, setError] = useState("");

  const cargar = useCallback(async () => {
    try {
      setE(await api<Expediente>(`/estudiantes/${id}/expediente`));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al cargar");
    }
  }, [id]);
  useEffect(() => { cargar(); }, [cargar]);

  if (!e) return <section>{error ? <p className="error" role="alert">{error}</p> : <p>Cargando…</p>}</section>;
  const actual = e.ciclo_actual;

  async function sancionar(cuerpo: object) {
    setError("");
    try {
      setE(await api<Expediente>(`/estudiantes/${id}/sancion-acumulacion`, { method: "POST", body: JSON.stringify(cuerpo) }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo aplicar la sanción");
    }
  }

  return (
    <section>
      <p><Link to={`/estudiantes/${e.estudiante_id}`}>← Ficha del estudiante</Link> · <Link to={`/reportes?estudiante_id=${e.estudiante_id}`}>Todos sus reportes</Link></p>
      <h1>Expediente disciplinario</h1>
      <p>{e.estudiante} · {e.numero_control} · Grupo {e.grupo_actual ?? "—"} · {e.total_reportes} reporte(s) en toda su carrera</p>
      {error && <p className="error" role="alert">{error}</p>}

      <div className="tarjeta">
        <h2>Ciclo actual</h2>
        {actual ? (
          <>
            <p className="contador"><strong>{actual.contables}</strong> de {e.umbral} reportes
              {actual.listo_para_sancion && <span className="badge alerta">Procede sanción</span>}</p>
            <p><small>Cuentan los reportes no cancelados y sin sanción directa. Una sanción directa no reinicia el contador; solo la sanción por acumulación lo hace.</small></p>
            <TablaReportes ciclo={actual} />
          </>
        ) : <p>Sin reportes en el ciclo actual (contador en 0).</p>}
        {actual?.listo_para_sancion && puede("APLICAR_SANCIONES") && (
          <div className="tarjeta" style={{ marginTop: "1rem" }}>
            <p>La sanción cubrirá los {actual.contables} reportes del ciclo, los concluirá y reiniciará el contador. Cada uno necesita al menos una llamada Realizada o Atendida.</p>
            <FormularioSancion titulo="Sanción por acumulación" textoBoton="Aplicar sanción y cerrar el ciclo"
              confirmacion={`Se sancionará por acumulación y se concluirán ${actual.contables} reportes. ¿Continuar?`} alEnviar={sancionar} />
          </div>
        )}
      </div>

      {e.sanciones_directas.length > 0 && (
        <div className="tarjeta"><h2>Sanciones directas</h2>{e.sanciones_directas.map((s) => <TarjetaSancion key={s.id} s={s} />)}</div>
      )}

      {e.ciclos_anteriores.slice().reverse().map((c) => (
        <div className="tarjeta" key={c.numero}>
          <h2>Ciclo {c.numero} (cerrado {fechaLocal(c.fecha_cierre)})</h2>
          {c.sancion && <TarjetaSancion s={c.sancion} />}
          <TablaReportes ciclo={c} />
        </div>
      ))}
    </section>
  );
}
