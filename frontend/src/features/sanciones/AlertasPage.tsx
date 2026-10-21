import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../../shared/api/client";
import { fechaLocal } from "../reportes/api";

interface Alerta {
  id: number; tipo: "REPORTE_GRAVE" | "ACUMULACION"; titulo: string; mensaje: string; reporte_id: number | null;
  estudiante_id: number | null; creada_en: string; correo_enviado: boolean; correo_error: string | null;
  atendida: boolean; atendida_en: string | null;
}

export function AlertasPage() {
  const [alertas, setAlertas] = useState<Alerta[]>([]);
  const [pendientes, setPendientes] = useState(0);
  const [verTodas, setVerTodas] = useState(false);
  const [error, setError] = useState("");

  const cargar = useCallback(async () => {
    try {
      const r = await api<{ pendientes: number; alertas: Alerta[] }>(`/alertas?pendientes=${!verTodas}`);
      setAlertas(r.alertas);
      setPendientes(r.pendientes);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al cargar");
    }
  }, [verTodas]);
  useEffect(() => { cargar(); }, [cargar]);

  async function atender(a: Alerta) {
    try {
      await api(`/alertas/${a.id}/atendida`, { method: "POST" });
      await cargar();
      window.dispatchEvent(new Event("alertas-cambiaron"));
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo marcar la alerta");
    }
  }

  return (
    <section>
      <h1>Alertas {pendientes > 0 && <span className="badge alerta">{pendientes}</span>}</h1>
      <p>Reportes <strong>Grave</strong> o <strong>Muy grave</strong> y estudiantes que llegan a <strong>3 reportes</strong> en su ciclo.</p>
      <label><input type="checkbox" checked={verTodas} onChange={(e) => setVerTodas(e.target.checked)} /> Incluir las ya atendidas</label>
      {error && <p className="error" role="alert">{error}</p>}
      {alertas.length === 0 && <p>No hay alertas {verTodas ? "" : "pendientes"}.</p>}
      {alertas.map((a) => (
        <div key={a.id} className={`tarjeta alerta-item ${a.atendida ? "atendida" : ""}`} style={{ marginTop: "0.8rem" }}>
          <strong>{a.titulo}</strong> <small>· {fechaLocal(a.creada_en)}</small>
          <p style={{ margin: "0.3rem 0" }}>{a.mensaje}</p>
          <div className="fila-botones" style={{ marginBottom: 0 }}>
            {a.reporte_id && <Link to={`/reportes/${a.reporte_id}`}>Ver reporte</Link>}
            {a.tipo === "ACUMULACION" && a.estudiante_id && <Link to={`/estudiantes/${a.estudiante_id}/expediente`}>Ver expediente y sancionar</Link>}
            {!a.atendida && <button className="secundario" onClick={() => atender(a)}>Marcar como vista</button>}
            <small>{a.correo_enviado ? "Correo enviado" : `Correo no enviado${a.correo_error ? `: ${a.correo_error}` : ""}`}</small>
          </div>
        </div>
      ))}
    </section>
  );
}
