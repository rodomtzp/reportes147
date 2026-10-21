import { ReactNode, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../../app/AuthContext";
import { Dashboard, obtenerDashboard, Rango } from "./api";
import { Barras, SerieTiempo, TarjetaGrafica } from "./graficas";

const RANGOS: { valor: Rango; texto: string }[] = [
  { valor: "periodo", texto: "Periodo escolar" },
  { valor: "mes", texto: "Mes actual" },
  { valor: "30dias", texto: "Últimos 30 días" },
];
// Escala ordinal de un solo tono: más oscuro = más grave.
const COLORES_GRAVEDAD = ["#86b6ef", "#5598e7", "#256abf", "#104281"];

const fecha = (iso: string) => new Date(`${iso}T12:00:00`).toLocaleDateString("es-MX", { day: "numeric", month: "short", year: "numeric" });

function Indicador({ titulo, valor, pie, aviso, a }: { titulo: string; valor: number | string; pie?: ReactNode; aviso?: boolean; a?: string }) {
  const contenido = (
    <>
      <span className="ind-titulo">{titulo}</span>
      <span className={`ind-valor${aviso && Number(valor) > 0 ? " ind-alerta" : ""}`}>{valor}</span>
      {pie && <span className="ind-pie">{pie}</span>}
    </>
  );
  return a ? <Link to={a} className="indicador enlace">{contenido}</Link> : <div className="indicador">{contenido}</div>;
}

function ComparacionMes({ actual, anterior }: { actual: number; anterior: number }) {
  const dif = actual - anterior;
  if (anterior === 0 && actual === 0) return <>Sin reportes este mes ni el anterior</>;
  const signo = dif === 0 ? "igual que" : dif > 0 ? `▲ ${dif} más que` : `▼ ${Math.abs(dif)} menos que`;
  return <>Este mes: {actual} · {signo} el mes anterior ({anterior})</>;
}

export function HomePage() {
  const { usuario, puede } = useAuth();
  const [rango, setRango] = useState<Rango>("periodo");
  const [d, setD] = useState<Dashboard | null>(null);
  const [error, setError] = useState("");
  const tutor = (usuario?.grupos_tutelados.length ?? 0) > 0;

  useEffect(() => {
    let vigente = true;
    setError("");
    obtenerDashboard(rango)
      .then((r) => { if (vigente) setD(r); })
      .catch((e) => { if (vigente) setError(e instanceof Error ? e.message : "No se pudo cargar el panel"); });
    return () => { vigente = false; };
  }, [rango]);

  const enlaceEstudiante = (id: number) =>
    puede("VER_TODOS_LOS_REPORTES") ? `/estudiantes/${id}/expediente` : tutor ? `/estudiantes/${id}` : undefined;

  return (
    <section className="dashboard">
      <header className="dash-cabecera">
        <div>
          <h1>Bienvenido, {usuario?.nombre}</h1>
          <p className="viz-sub">
            {d?.alcance === "total" && "Reportes de todo el plantel"}
            {d?.alcance === "propio" && (tutor ? "Reportes de tus grupos y los que tú generaste" : "Reportes que tú generaste")}
            {d && d.alcance !== "ninguno" && <> · {d.periodo && d.rango === "periodo" ? `${d.periodo}: ` : ""}{fecha(d.desde)} al {fecha(d.hasta)}</>}
          </p>
        </div>
        {d && d.alcance !== "ninguno" && (
          <div className="segmentos" role="group" aria-label="Rango de tiempo">
            {RANGOS.map((r) => (
              <button key={r.valor} type="button" aria-pressed={d.rango === r.valor} className={d.rango === r.valor ? "activo" : ""}
                onClick={() => setRango(r.valor)}>{r.texto}</button>
            ))}
          </div>
        )}
      </header>

      {error && <p className="error" role="alert">{error}</p>}
      {!d && !error && <p>Cargando…</p>}

      {d && d.alcance === "ninguno" && (
        <ul>
          {puede("CREAR_REPORTE") && <li>Genera un reporte desde <strong>Nuevo reporte</strong>.</li>}
          {puede("GESTIONAR_USUARIOS") && <li>Administración de usuarios y catálogos: usa el menú superior.</li>}
          {puede("IMPORTAR_ESTUDIANTES") && <li><Link to="/importar-estudiantes">Importar estudiantes</Link></li>}
        </ul>
      )}

      {d && d.alcance !== "ninguno" && (
        <>
          <div className="indicadores">
            <Indicador titulo={RANGOS.find((r) => r.valor === d.rango)!.texto} valor={d.total_rango} pie={<ComparacionMes actual={d.mes_actual} anterior={d.mes_anterior} />} a="/reportes" />
            {d.pendientes_llamada !== null && (
              <Indicador titulo="Pendientes de llamada" valor={d.pendientes_llamada} pie="Sin llamada realizada a los padres" aviso a="/reportes?sin_llamada=true" />
            )}
            <Indicador titulo="Con 2 o más reportes" valor={d.total_en_riesgo}
              pie={d.listos_para_sancion > 0 ? `${d.listos_para_sancion} ya llegaron a 3 (sanción por acumulación)` : "Cerca de las 3 faltas del ciclo"} aviso />
            {d.alertas_pendientes !== null && (
              <Indicador titulo="Alertas pendientes" valor={d.alertas_pendientes} pie="Graves y acumulaciones por atender" aviso a="/alertas" />
            )}
          </div>

          <div className="dash-rejilla">
            <TarjetaGrafica titulo="Reportes en el tiempo" subtitulo={d.granularidad === "semana" ? "Por semana" : "Por día"}>
              <SerieTiempo datos={d.serie} granularidad={d.granularidad} />
            </TarjetaGrafica>
            <TarjetaGrafica titulo="Por gravedad" subtitulo="Más oscuro, más grave">
              <Barras datos={d.por_gravedad.map((g) => ({ etiqueta: g.etiqueta, valor: g.valor }))} columna="Gravedad" colores={COLORES_GRAVEDAD} />
            </TarjetaGrafica>
            <TarjetaGrafica titulo="Por estado">
              <Barras datos={d.por_estado} columna="Estado" />
            </TarjetaGrafica>
            <TarjetaGrafica titulo="Por tipo de incidencia" subtitulo="Las más frecuentes">
              <Barras datos={d.por_tipo} columna="Incidencia" />
            </TarjetaGrafica>
            <TarjetaGrafica titulo="Por grupo" subtitulo="Los 10 con más reportes">
              <Barras datos={d.por_grupo} columna="Grupo" />
            </TarjetaGrafica>
            {d.alcance === "total" && (
              <TarjetaGrafica titulo="Por carrera">
                <Barras datos={d.por_carrera} columna="Carrera" />
              </TarjetaGrafica>
            )}
          </div>

          {d.en_riesgo.length > 0 && (
            <section className="tarjeta">
              <h2>Estudiantes cerca de la sanción por acumulación</h2>
              <table>
                <thead><tr><th>Estudiante</th><th>Grupo</th><th>Reportes en el ciclo</th></tr></thead>
                <tbody>
                  {d.en_riesgo.map((e) => {
                    const a = enlaceEstudiante(e.estudiante_id);
                    return (
                      <tr key={e.estudiante_id}>
                        <td>{a ? <Link to={a}>{e.estudiante}</Link> : e.estudiante}</td>
                        <td>{e.grupo ?? "—"}</td>
                        <td>{e.total}{e.total >= 3 ? " — lista para sanción" : ""}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
              {d.total_en_riesgo > d.en_riesgo.length && <p className="viz-sub">Se muestran {d.en_riesgo.length} de {d.total_en_riesgo}.</p>}
            </section>
          )}
        </>
      )}
    </section>
  );
}
