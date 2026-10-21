import { useEffect, useState } from "react";
import { useAuth } from "../../app/AuthContext";
import { api, descargar } from "../../shared/api/client";

interface Carrera { id: number; nombre: string }

interface Props {
  estudianteId?: string | null;
  grupoId?: string;
  desde?: string;
  hasta?: string;
}

/** Descarga de Excel por estudiante, grupo o carrera, según los filtros vigentes. Solo exporta lo que el usuario puede ver. */
export function PanelExportar({ estudianteId, grupoId, desde, hasta }: Props) {
  const { puede, usuario } = useAuth();
  const [carreras, setCarreras] = useState<Carrera[]>([]);
  const [carreraId, setCarreraId] = useState("");
  const [contacto, setContacto] = useState(false);
  const [error, setError] = useState("");
  const [bajando, setBajando] = useState(false);
  const verTodo = puede("VER_TODOS_LOS_REPORTES");
  const puedeContacto = puede("VER_DATOS_CONTACTO") || (usuario?.grupos_tutelados.length ?? 0) > 0;

  useEffect(() => {
    if (verTodo) api<Carrera[]>("/carreras").then(setCarreras).catch(() => undefined);
  }, [verTodo]);

  if (!puede("EXPORTAR_EXCEL") && (usuario?.grupos_tutelados.length ?? 0) === 0) return null;

  async function bajar(ruta: string, nombre: string) {
    setError("");
    setBajando(true);
    const p = new URLSearchParams();
    if (desde) p.set("desde", desde);
    if (hasta) p.set("hasta", hasta);
    if (contacto && puedeContacto) p.set("incluir_contacto", "true");
    try {
      await descargar(`${ruta}?${p}`, nombre);
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo exportar");
    } finally {
      setBajando(false);
    }
  }

  return (
    <fieldset className="formulario">
      <legend>Exportar a Excel</legend>
      {estudianteId && (
        <button disabled={bajando} onClick={() => bajar(`/exportaciones/estudiantes/${estudianteId}`, "reportes-estudiante.xlsx")}>
          Este estudiante
        </button>
      )}
      <button disabled={bajando || !grupoId} title={grupoId ? "" : "Elige un grupo en el filtro"}
        onClick={() => bajar(`/exportaciones/grupos/${grupoId}`, "reportes-grupo.xlsx")}>
        Grupo seleccionado
      </button>
      {verTodo && (
        <>
          <select value={carreraId} onChange={(e) => setCarreraId(e.target.value)} aria-label="Carrera a exportar">
            <option value="">Carrera…</option>
            {carreras.map((c) => <option key={c.id} value={c.id}>{c.nombre}</option>)}
          </select>
          <button disabled={bajando || !carreraId} onClick={() => bajar(`/exportaciones/carreras/${carreraId}`, "reportes-carrera.xlsx")}>
            Carrera
          </button>
        </>
      )}
      {puedeContacto && (
        <label>
          <input type="checkbox" checked={contacto} onChange={(e) => setContacto(e.target.checked)} />
          Incluir teléfono, correo y domicilio (queda en la bitácora)
        </label>
      )}
      <small>Se respetan el rango de fechas y los permisos. Máximo 5000 reportes por archivo.</small>
      {error && <p className="error" role="alert">{error}</p>}
    </fieldset>
  );
}
