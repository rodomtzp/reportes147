import { FormEvent, ReactNode, useCallback, useEffect, useState } from "react";
import { api } from "../api/client";

export interface Opcion { valor: string | number; etiqueta: string }

export interface Campo {
  nombre: string;
  etiqueta: string;
  tipo: "texto" | "numero" | "booleano" | "fecha" | "select";
  requerido?: boolean;
  soloCreacion?: boolean; // no se envía al editar
  soloEdicion?: boolean; // no se envía al crear (p. ej. "activo")
  opciones?: Opcion[];
  opcionesDe?: { ruta: string; valor: string; etiqueta: (fila: any) => string };
  min?: number;
  max?: number;
  maxLength?: number;
}

export type OpcionesCargadas = Record<string, Opcion[]>;

export interface Columna {
  titulo: string;
  valor: (fila: any, opciones: OpcionesCargadas) => ReactNode;
}

interface Props {
  titulo: string;
  ruta: string;
  campos: Campo[];
  columnas: Columna[];
  editable?: boolean;
  eliminable?: boolean;
  puedeEditar?: (fila: any) => boolean;
  acciones?: (fila: any, recargar: () => void) => ReactNode;
}

export const etiquetaDe = (opciones: OpcionesCargadas, campo: string, valor: unknown): string =>
  opciones[campo]?.find((o) => String(o.valor) === String(valor))?.etiqueta ?? String(valor);

export const si_no = (v: boolean) => (v ? "Sí" : "No");

function vacios(campos: Campo[]): Record<string, any> {
  const v: Record<string, any> = {};
  campos.forEach((c) => (v[c.nombre] = c.tipo === "booleano" ? false : ""));
  return v;
}

export function CrudPage({ titulo, ruta, campos, columnas, editable = true, eliminable = false, puedeEditar, acciones }: Props) {
  const [filas, setFilas] = useState<any[]>([]);
  const [dinamicas, setDinamicas] = useState<OpcionesCargadas>({});
  const [valores, setValores] = useState<Record<string, any>>(vacios(campos));
  const [editandoId, setEditandoId] = useState<number | null>(null);
  const [error, setError] = useState("");

  const cargar = useCallback(async () => {
    try {
      setFilas(await api<any[]>(ruta));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al cargar");
    }
  }, [ruta]);

  useEffect(() => {
    cargar();
    campos.forEach((c) => {
      if (!c.opcionesDe) return;
      const od = c.opcionesDe;
      api<any[]>(od.ruta)
        .then((datos) =>
          setDinamicas((prev) => ({ ...prev, [c.nombre]: datos.map((d) => ({ valor: d[od.valor], etiqueta: od.etiqueta(d) })) }))
        )
        .catch(() => undefined);
    });
  }, [cargar, campos]);

  const opcionesDe = (c: Campo): Opcion[] => c.opciones ?? dinamicas[c.nombre] ?? [];

  function cuerpo(): Record<string, unknown> {
    const salida: Record<string, unknown> = {};
    for (const c of campos) {
      if (editandoId === null && c.soloEdicion) continue;
      if (editandoId !== null && c.soloCreacion) continue;
      const v = valores[c.nombre];
      if (c.tipo === "booleano") salida[c.nombre] = !!v;
      else if (v === "" || v === undefined) continue;
      else if (c.tipo === "numero") salida[c.nombre] = Number(v);
      else if (c.tipo === "select") salida[c.nombre] = opcionesDe(c).find((o) => String(o.valor) === String(v))?.valor ?? v;
      else salida[c.nombre] = v;
    }
    return salida;
  }

  async function enviar(e: FormEvent) {
    e.preventDefault();
    setError("");
    try {
      if (editandoId === null) await api(ruta, { method: "POST", body: JSON.stringify(cuerpo()) });
      else await api(`${ruta}/${editandoId}`, { method: "PATCH", body: JSON.stringify(cuerpo()) });
      cancelar();
      await cargar();
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo guardar");
    }
  }

  function editar(fila: any) {
    setError("");
    setEditandoId(fila.id);
    const v = vacios(campos);
    campos.forEach((c) => (v[c.nombre] = fila[c.nombre] ?? v[c.nombre]));
    setValores(v);
  }

  function cancelar() {
    setEditandoId(null);
    setValores(vacios(campos));
  }

  async function eliminar(fila: any) {
    if (!window.confirm("¿Seguro que deseas continuar?")) return;
    setError("");
    try {
      await api(`${ruta}/${fila.id}`, { method: "DELETE" });
      await cargar();
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo eliminar");
    }
  }

  const visibles = campos.filter((c) => (editandoId === null ? !c.soloEdicion : !c.soloCreacion));

  return (
    <section>
      <h1>{titulo}</h1>
      {(editandoId === null ? campos.some((c) => !c.soloEdicion) : editable) && (
        <form className="formulario" onSubmit={enviar}>
          {visibles.map((c) => (
            <label key={c.nombre}>
              {c.etiqueta}
              {c.tipo === "booleano" ? (
                <input type="checkbox" checked={!!valores[c.nombre]} onChange={(e) => setValores({ ...valores, [c.nombre]: e.target.checked })} />
              ) : c.tipo === "select" ? (
                <select required={c.requerido} value={valores[c.nombre]} onChange={(e) => setValores({ ...valores, [c.nombre]: e.target.value })}>
                  <option value="">— Selecciona —</option>
                  {opcionesDe(c).map((o) => (
                    <option key={String(o.valor)} value={String(o.valor)}>{o.etiqueta}</option>
                  ))}
                </select>
              ) : (
                <input
                  type={c.tipo === "numero" ? "number" : c.tipo === "fecha" ? "date" : "text"}
                  required={c.requerido}
                  min={c.min}
                  max={c.max}
                  maxLength={c.maxLength}
                  value={valores[c.nombre]}
                  onChange={(e) => setValores({ ...valores, [c.nombre]: e.target.value })}
                />
              )}
            </label>
          ))}
          <button type="submit">{editandoId === null ? "Agregar" : "Guardar cambios"}</button>
          {editandoId !== null && <button type="button" className="secundario" onClick={cancelar}>Cancelar</button>}
        </form>
      )}
      {error && <p className="error" role="alert">{error}</p>}
      <table>
        <thead>
          <tr>
            {columnas.map((c) => <th key={c.titulo}>{c.titulo}</th>)}
            {(editable || eliminable || acciones) && <th>Acciones</th>}
          </tr>
        </thead>
        <tbody>
          {filas.map((fila) => (
            <tr key={fila.id}>
              {columnas.map((c) => <td key={c.titulo}>{c.valor(fila, dinamicas)}</td>)}
              {(editable || eliminable || acciones) && (
                <td className="acciones">
                  {editable && (puedeEditar?.(fila) ?? true) && <button className="secundario" onClick={() => editar(fila)}>Editar</button>}
                  {eliminable && <button className="peligro" onClick={() => eliminar(fila)}>Retirar</button>}
                  {acciones?.(fila, cargar)}
                </td>
              )}
            </tr>
          ))}
          {filas.length === 0 && <tr><td colSpan={columnas.length + 1}>Sin registros.</td></tr>}
        </tbody>
      </table>
    </section>
  );
}
