import { useEffect, useRef, useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import { api } from "../api/client";
import { useAuth } from "../../app/AuthContext";

interface Enlace { a: string; t: string; ver: boolean; fin?: boolean }
interface Grupo { t: string; items: Enlace[] }
type Entrada = Enlace | Grupo;

/** Menú desplegable: se cierra al elegir una opción, al hacer clic fuera o con Escape. */
function Desplegable({ titulo, items, activo, derecha = false }: { titulo: string; items: Enlace[]; activo: boolean; derecha?: boolean }) {
  const [abierto, setAbierto] = useState(false);
  const caja = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!abierto) return;
    const fuera = (e: MouseEvent) => { if (!caja.current?.contains(e.target as Node)) setAbierto(false); };
    const tecla = (e: KeyboardEvent) => { if (e.key === "Escape") setAbierto(false); };
    document.addEventListener("mousedown", fuera);
    document.addEventListener("keydown", tecla);
    return () => { document.removeEventListener("mousedown", fuera); document.removeEventListener("keydown", tecla); };
  }, [abierto]);
  return (
    <div className="menu-grupo" ref={caja}>
      <button type="button" className={`menu-boton${activo ? " active" : ""}`} aria-expanded={abierto} aria-haspopup="true"
        onClick={() => setAbierto(!abierto)}>
        {titulo} <span aria-hidden="true">▾</span>
      </button>
      {abierto && (
        <div className={`menu-lista${derecha ? " derecha" : ""}`} role="menu">
          {items.map((i) => (
            <NavLink key={i.a} to={i.a} end={i.fin !== false} role="menuitem" onClick={() => setAbierto(false)}
              className={({ isActive }) => (isActive ? "active" : "")}>
              {i.t}
            </NavLink>
          ))}
        </div>
      )}
    </div>
  );
}

export function Layout() {
  const { usuario, salir, puede } = useAuth();
  const ubicacion = useLocation();
  const [movil, setMovil] = useState(false);
  const admin = puede("ADMINISTRAR_CATALOGOS");
  const verAlertas = puede("VER_ALERTAS");
  const [pendientes, setPendientes] = useState(0);

  useEffect(() => { setMovil(false); }, [ubicacion.pathname]);
  useEffect(() => {
    if (!verAlertas) return;
    const cargar = () => api<{ pendientes: number }>("/alertas/resumen").then((r) => setPendientes(r.pendientes)).catch(() => undefined);
    cargar();
    const t = setInterval(cargar, 60000);  // se refresca cada minuto
    window.addEventListener("alertas-cambiaron", cargar);
    return () => { clearInterval(t); window.removeEventListener("alertas-cambiaron", cargar); };
  }, [verAlertas]);

  const tutor = (usuario?.grupos_tutelados.length ?? 0) > 0;
  const verEstudiantes = puede("GESTIONAR_ESTUDIANTES") || puede("VER_DATOS_CONTACTO") || tutor;
  const verReportes = puede("VER_TODOS_LOS_REPORTES") || puede("VER_REPORTES_PROPIOS") || tutor;

  const entradas: Entrada[] = [
    { a: "/", t: "Inicio", ver: true },
    { a: "/reportes", t: "Reportes", ver: verReportes },
    { t: "Estudiantes", items: [
      { a: "/estudiantes", t: "Estudiantes", ver: verEstudiantes },
      { a: "/importar-estudiantes", t: "Importar estudiantes", ver: puede("IMPORTAR_ESTUDIANTES") },
      { a: "/avance-semestre", t: "Avance de semestre", ver: puede("AVANZAR_SEMESTRE") },
    ] },
    { a: "/alertas", t: "Alertas", ver: verAlertas },
    { t: "Administración", items: [
      { a: "/usuarios", t: "Usuarios", ver: puede("GESTIONAR_USUARIOS") },
      { a: "/tutores", t: "Tutores", ver: admin },
      { a: "/carreras", t: "Carreras", ver: admin },
      { a: "/grupos", t: "Grupos", ver: admin },
      { a: "/periodos", t: "Periodos escolares", ver: admin },
      { a: "/tipos-incidencia", t: "Tipos de incidencia", ver: admin },
      { a: "/tipos-sancion", t: "Tipos de sanción", ver: admin },
      { a: "/bitacora", t: "Bitácora de accesos", ver: puede("CONSULTAR_BITACORA") },
    ] },
  ];
  const estaEn = (a: string) => (a === "/" ? ubicacion.pathname === "/" : ubicacion.pathname.startsWith(a));

  return (
    <>
      <header className="nav">
        <strong className="marca">CBTis 147</strong>
        <button type="button" className="hamburguesa" aria-label="Menú" aria-expanded={movil} onClick={() => setMovil(!movil)}>☰</button>
        <nav className={`menu${movil ? " abierto" : ""}`} aria-label="Principal">
          {puede("CREAR_REPORTE") && (
            <NavLink to="/reportes/nuevo" className="accion-principal">+ Nuevo reporte</NavLink>
          )}
          {entradas.map((e) => {
            if ("items" in e) {
              const visibles = e.items.filter((i) => i.ver);
              if (visibles.length === 0) return null;
              if (visibles.length === 1) {  // un solo destino: enlace directo, sin desplegable
                const u = visibles[0];
                return <NavLink key={u.a} to={u.a} className={({ isActive }) => (isActive || estaEn(u.a) ? "active" : "")}>{e.t}</NavLink>;
              }
              return <Desplegable key={e.t} titulo={e.t} items={visibles} activo={visibles.some((i) => estaEn(i.a))} />;
            }
            if (!e.ver) return null;
            return (
              <NavLink key={e.a} to={e.a} end={e.a === "/"} className={({ isActive }) => (isActive ? "active" : "")}>
                {e.t}
                {e.a === "/alertas" && pendientes > 0 && <span className="badge alerta" aria-label={`${pendientes} pendientes`}>{pendientes}</span>}
              </NavLink>
            );
          })}
          <span className="espacio" />
          <Desplegable titulo={usuario?.nombre ?? "Cuenta"} derecha activo={false}
            items={[{ a: "/cambiar-password", t: "Cambiar contraseña", ver: true }]} />
          <button type="button" className="salir" onClick={salir}>Salir</button>
        </nav>
      </header>
      <main className="contenido">
        <Outlet />
      </main>
    </>
  );
}
