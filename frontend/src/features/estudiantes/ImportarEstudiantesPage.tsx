import { FormEvent, useRef, useState } from "react";
import { api, descargar } from "../../shared/api/client";

interface Problema { fila: number; numero_control: string; motivo: string }
interface Resultado { creados: number; omitidos: Problema[]; errores: Problema[] }

function Tabla({ titulo, filas }: { titulo: string; filas: Problema[] }) {
  if (filas.length === 0) return null;
  return (
    <div className="tarjeta">
      <h2>{titulo} ({filas.length})</h2>
      <table>
        <thead><tr><th>Fila</th><th>Número de control</th><th>Motivo</th></tr></thead>
        <tbody>{filas.map((f, i) => <tr key={i}><td>{f.fila}</td><td>{f.numero_control || "—"}</td><td>{f.motivo}</td></tr>)}</tbody>
      </table>
    </div>
  );
}

export function ImportarEstudiantesPage() {
  const entrada = useRef<HTMLInputElement>(null);
  const [resultado, setResultado] = useState<Resultado | null>(null);
  const [error, setError] = useState("");
  const [enviando, setEnviando] = useState(false);

  async function enviar(e: FormEvent) {
    e.preventDefault();
    const archivo = entrada.current?.files?.[0];
    if (!archivo) return setError("Selecciona un archivo .csv o .xlsx.");
    setError("");
    setResultado(null);
    setEnviando(true);
    try {
      const datos = new FormData();
      datos.append("archivo", archivo);
      setResultado(await api<Resultado>("/estudiantes/importar", { method: "POST", body: datos }));
      if (entrada.current) entrada.current.value = "";
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo importar");
    } finally {
      setEnviando(false);
    }
  }

  return (
    <section>
      <h1>Importar estudiantes</h1>
      <div className="tarjeta">
        <p>
          Sube un archivo <strong>.csv</strong> o <strong>.xlsx</strong> (máximo 2 MB y 2,000 filas). Se crean los estudiantes nuevos
          y se inscriben en su grupo del <strong>periodo vigente</strong>. Los números de control que ya existen se omiten y se
          reportan; las filas con datos inválidos se listan para que las corrijas y las vuelvas a subir.
        </p>
        <p>Columnas obligatorias: numero_control, primer_apellido, nombres, generacion, grupo (ej. 1G), tutor_nombre, tutor_telefono.</p>
        <button className="secundario" type="button" onClick={() => descargar("/estudiantes/plantilla", "plantilla_estudiantes.csv").catch((e) => setError(e.message))}>
          Descargar plantilla
        </button>
      </div>
      <form className="formulario" onSubmit={enviar}>
        <label>Archivo<input ref={entrada} type="file" accept=".csv,.xlsx" /></label>
        <button disabled={enviando}>{enviando ? "Importando…" : "Importar"}</button>
      </form>
      {error && <p className="error" role="alert">{error}</p>}
      {resultado && (
        <>
          <p className="ok" role="status"><strong>{resultado.creados}</strong> estudiantes creados.</p>
          <Tabla titulo="Omitidos" filas={resultado.omitidos} />
          <Tabla titulo="Con errores (no se importaron)" filas={resultado.errores} />
        </>
      )}
    </section>
  );
}
