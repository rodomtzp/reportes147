import { FormEvent, useCallback, useEffect, useState } from "react";
import { api } from "../../shared/api/client";
import { fechaLocal } from "../reportes/api";

interface Registro {
  id: number; accion: "EXPORTACION" | "CONSULTA_CONTACTO"; usuario: string; fecha: string;
  descripcion: string; estudiante: string | null; filas: number | null; con_contacto: boolean;
}

const ETIQUETA = { EXPORTACION: "Exportación", CONSULTA_CONTACTO: "Consulta de contacto" } as const;
const POR_PAGINA = 100;

export function BitacoraPage() {
  const [registros, setRegistros] = useState<Registro[]>([]);
  const [f, setF] = useState({ accion: "", desde: "", hasta: "" });
  const [pagina, setPagina] = useState(0);
  const [error, setError] = useState("");

  const cargar = useCallback(async (nuevaPagina = 0) => {
    setError("");
    const p = new URLSearchParams({ limite: String(POR_PAGINA), offset: String(nuevaPagina * POR_PAGINA) });
    (["accion", "desde", "hasta"] as const).forEach((k) => f[k] && p.set(k, f[k]));
    try {
      setRegistros(await api<Registro[]>(`/bitacora?${p}`));
      setPagina(nuevaPagina);
    } catch (e) {
      setRegistros([]);
      setError(e instanceof Error ? e.message : "Error al cargar");
    }
  }, [f]);

  useEffect(() => { cargar(0); /* eslint-disable-next-line react-hooks/exhaustive-deps */ }, []);

  const filtrar = (e: FormEvent) => { e.preventDefault(); cargar(0); };

  return (
    <section>
      <h1>Bitácora de accesos</h1>
      <p>Quién consultó teléfonos o domicilios y quién exportó información.</p>
      <form className="formulario" onSubmit={filtrar}>
        <label>Acción
          <select value={f.accion} onChange={(e) => setF({ ...f, accion: e.target.value })}>
            <option value="">Todas</option>
            <option value="EXPORTACION">Exportaciones</option>
            <option value="CONSULTA_CONTACTO">Consultas de contacto</option>
          </select>
        </label>
        <label>Desde<input type="date" value={f.desde} onChange={(e) => setF({ ...f, desde: e.target.value })} /></label>
        <label>Hasta<input type="date" value={f.hasta} onChange={(e) => setF({ ...f, hasta: e.target.value })} /></label>
        <button type="submit">Filtrar</button>
      </form>
      {error && <p className="error" role="alert">{error}</p>}
      <table>
        <thead><tr><th>Fecha</th><th>Usuario</th><th>Acción</th><th>Detalle</th><th>Filas</th><th>Contacto</th></tr></thead>
        <tbody>
          {registros.map((r) => (
            <tr key={r.id}>
              <td>{fechaLocal(r.fecha)}</td><td>{r.usuario}</td><td>{ETIQUETA[r.accion]}</td>
              <td>{r.descripcion}</td><td>{r.filas ?? "—"}</td><td>{r.con_contacto ? "Sí" : "No"}</td>
            </tr>
          ))}
          {registros.length === 0 && <tr><td colSpan={6}>Sin registros.</td></tr>}
        </tbody>
      </table>
      <p>
        <button disabled={pagina === 0} onClick={() => cargar(pagina - 1)}>Anterior</button>{" "}
        <button disabled={registros.length < POR_PAGINA} onClick={() => cargar(pagina + 1)}>Siguiente</button>
      </p>
    </section>
  );
}
