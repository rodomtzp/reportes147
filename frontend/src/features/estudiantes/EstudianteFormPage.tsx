import { FormEvent, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../../shared/api/client";
import { Detalle, Grupo } from "./api";

const VACIO = {
  numero_control: "", primer_apellido: "", segundo_apellido: "", nombres: "", telefono: "", correo: "",
  calle: "", numero: "", colonia: "", ciudad: "", generacion: "", grupo_id: "",
};
const TUTOR_VACIO = { nombre: "", parentesco: "", telefono: "", correo: "" };

export function EstudianteFormPage() {
  const navegar = useNavigate();
  const [f, setF] = useState(VACIO);
  const [t, setT] = useState(TUTOR_VACIO);
  const [grupos, setGrupos] = useState<Grupo[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    api<Grupo[]>("/grupos?solo_activos=true").then(setGrupos).catch(() => undefined);
  }, []);

  const campo = (nombre: keyof typeof VACIO, etiqueta: string, requerido = false, tipo = "text") => (
    <label>
      {etiqueta}
      <input type={tipo} required={requerido} value={f[nombre]} onChange={(e) => setF({ ...f, [nombre]: e.target.value })} />
    </label>
  );
  const limpio = (o: Record<string, string>) => Object.fromEntries(Object.entries(o).filter(([, v]) => v.trim() !== ""));

  async function enviar(e: FormEvent) {
    e.preventDefault();
    setError("");
    try {
      const { grupo_id, ...datos } = f;
      const creado = await api<Detalle>("/estudiantes", {
        method: "POST",
        body: JSON.stringify({ ...limpio(datos), grupo_id: Number(grupo_id), tutores: [{ ...limpio(t), es_principal: true }] }),
      });
      navegar(`/estudiantes/${creado.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo guardar");
    }
  }

  return (
    <section>
      <h1>Nuevo estudiante</h1>
      <form onSubmit={enviar}>
        <div className="tarjeta">
          <h2>Datos del estudiante</h2>
          <div className="formulario sin-marco">
            {campo("numero_control", "Número de control", true)}
            {campo("primer_apellido", "Primer apellido", true)}
            {campo("segundo_apellido", "Segundo apellido")}
            {campo("nombres", "Nombre(s)", true)}
            {campo("telefono", "Teléfono", false, "tel")}
            {campo("correo", "Correo electrónico", false, "email")}
            {campo("generacion", "Generación (ej. 2024-2027)", true)}
            <label>
              Grupo actual
              <select required value={f.grupo_id} onChange={(e) => setF({ ...f, grupo_id: e.target.value })}>
                <option value="">— Selecciona —</option>
                {grupos.map((g) => <option key={g.id} value={g.id}>{g.clave}</option>)}
              </select>
            </label>
          </div>
        </div>
        <div className="tarjeta">
          <h2>Dirección</h2>
          <div className="formulario sin-marco">
            {campo("calle", "Calle")}{campo("numero", "Número")}{campo("colonia", "Colonia")}{campo("ciudad", "Ciudad")}
          </div>
        </div>
        <div className="tarjeta">
          <h2>Padre, madre o tutor legal (principal)</h2>
          <div className="formulario sin-marco">
            <label>Nombre<input required value={t.nombre} onChange={(e) => setT({ ...t, nombre: e.target.value })} /></label>
            <label>Parentesco<input value={t.parentesco} onChange={(e) => setT({ ...t, parentesco: e.target.value })} /></label>
            <label>Teléfono (10 dígitos)<input required type="tel" value={t.telefono} onChange={(e) => setT({ ...t, telefono: e.target.value })} /></label>
            <label>Correo<input type="email" value={t.correo} onChange={(e) => setT({ ...t, correo: e.target.value })} /></label>
          </div>
        </div>
        {error && <p className="error" role="alert">{error}</p>}
        <div className="fila-botones">
          <button type="submit">Guardar estudiante</button>
          <button type="button" className="secundario" onClick={() => navegar("/estudiantes")}>Cancelar</button>
        </div>
      </form>
    </section>
  );
}
