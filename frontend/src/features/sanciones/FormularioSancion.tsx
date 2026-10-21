import { FormEvent, useEffect, useState } from "react";
import { api } from "../../shared/api/client";
import { TipoSancion } from "../reportes/api";

interface Props {
  titulo: string;
  textoBoton: string;
  confirmacion: string;
  alEnviar: (cuerpo: { tipo_sancion_id: number; dias?: number; observaciones?: string }) => Promise<void>;
}

/** Selecciona el tipo de sanción (y los días si aplica) y pide confirmación antes de aplicarla. */
export function FormularioSancion({ titulo, textoBoton, confirmacion, alEnviar }: Props) {
  const [tipos, setTipos] = useState<TipoSancion[]>([]);
  const [tipoId, setTipoId] = useState("");
  const [dias, setDias] = useState("");
  const [obs, setObs] = useState("");
  const [enviando, setEnviando] = useState(false);

  useEffect(() => {
    api<TipoSancion[]>("/tipos-sancion?solo_activos=true").then(setTipos).catch(() => undefined);
  }, []);
  const tipo = tipos.find((t) => String(t.id) === tipoId);

  async function enviar(e: FormEvent) {
    e.preventDefault();
    if (!window.confirm(confirmacion)) return;
    setEnviando(true);
    try {
      await alEnviar({
        tipo_sancion_id: Number(tipoId),
        ...(tipo?.requiere_dias && dias ? { dias: Number(dias) } : {}),
        ...(obs.trim() ? { observaciones: obs } : {}),
      });
    } finally {
      setEnviando(false);
    }
  }

  return (
    <form onSubmit={enviar} className="form-apilado">
      <h2>{titulo}</h2>
      <label>Tipo de sanción
        <select required value={tipoId} onChange={(e) => setTipoId(e.target.value)}>
          <option value="">— Selecciona —</option>
          {tipos.map((t) => <option key={t.id} value={t.id}>{t.nombre}</option>)}
        </select>
      </label>
      {tipo?.requiere_dias && (
        <label>Número de días
          <input type="number" min={1} max={365} required value={dias} onChange={(e) => setDias(e.target.value)} />
        </label>
      )}
      <label>Observaciones (opcional)
        <textarea rows={3} maxLength={1000} value={obs} onChange={(e) => setObs(e.target.value)} />
      </label>
      <button className="peligro" type="submit" disabled={enviando}>{enviando ? "Aplicando…" : textoBoton}</button>
    </form>
  );
}

export const textoSancion = (s: { tipo: string; dias: number | null }) => (s.dias ? `${s.tipo} (${s.dias} días)` : s.tipo);
