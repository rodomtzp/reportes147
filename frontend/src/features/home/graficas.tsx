import { PointerEvent, ReactNode, useEffect, useRef, useState } from "react";
import { Par } from "./api";

const fechaCorta = (iso: string) =>
  new Date(`${iso}T12:00:00`).toLocaleDateString("es-MX", { day: "numeric", month: "short" });

/** Alternativa accesible: los mismos datos en tabla. */
function VerTabla({ datos, columna, formato }: { datos: Par[]; columna: string; formato?: (e: string) => string }) {
  return (
    <details className="viz-tabla">
      <summary>Ver como tabla</summary>
      <table>
        <thead><tr><th>{columna}</th><th>Reportes</th></tr></thead>
        <tbody>{datos.map((d) => <tr key={d.etiqueta}><td>{formato ? formato(d.etiqueta) : d.etiqueta}</td><td>{d.valor}</td></tr>)}</tbody>
      </table>
    </details>
  );
}

export function TarjetaGrafica({ titulo, subtitulo, children }: { titulo: string; subtitulo?: string; children: ReactNode }) {
  return (
    <section className="tarjeta viz">
      <h2>{titulo}</h2>
      {subtitulo && <p className="viz-sub">{subtitulo}</p>}
      {children}
    </section>
  );
}

interface BarrasProps {
  datos: Par[];
  columna: string;
  /** Un color por etiqueta (p. ej. escala de gravedad); si falta, todas usan la serie 1. */
  colores?: string[];
}

/** Barras horizontales: etiqueta, barra delgada con valor en la punta, anclada a una sola línea base. */
export function Barras({ datos, columna, colores }: BarrasProps) {
  const max = Math.max(1, ...datos.map((d) => d.valor));
  if (datos.every((d) => d.valor === 0)) return <p className="viz-vacio">Sin reportes en este rango.</p>;
  return (
    <>
      <div className="barras" role="img" aria-label={`Gráfica de barras por ${columna.toLowerCase()}`}>
        {datos.map((d, i) => (
          <div className="barras-fila" key={d.etiqueta} title={`${d.etiqueta}: ${d.valor}`}>
            <span className="barras-etiqueta">{d.etiqueta}</span>
            <span className="barras-pista">
              {d.valor > 0 && <span className="barras-barra" style={{ width: `${(d.valor / max) * 100}%`, background: colores?.[i] }} />}
              <span className="barras-valor">{d.valor}</span>
            </span>
          </div>
        ))}
      </div>
      <VerTabla datos={datos} columna={columna} />
    </>
  );
}

/** Línea de tiempo con área tenue, punto final y lectura al pasar el cursor. */
export function SerieTiempo({ datos, granularidad }: { datos: Par[]; granularidad: "dia" | "semana" }) {
  const [activo, setActivo] = useState<number | null>(null);
  // El dibujo usa el ancho real del contenedor: así el texto conserva su tamaño en cualquier pantalla.
  const caja = useRef<HTMLDivElement>(null);
  const [ancho, setAncho] = useState(640);
  useEffect(() => {
    const el = caja.current;
    if (!el || typeof ResizeObserver === "undefined") return;
    const obs = new ResizeObserver(() => setAncho(Math.max(280, Math.round(el.clientWidth))));
    obs.observe(el);
    setAncho(Math.max(280, Math.round(el.clientWidth)));
    return () => obs.disconnect();
  }, []);
  const W = ancho, H = 220, L = 34, R = 14, T = 12, B = 26;
  const max = Math.max(1, ...datos.map((d) => d.valor));
  const tope = max <= 4 ? 4 : Math.ceil(max / 4) * 4;       // eje con números redondos
  const x = (i: number) => L + (datos.length <= 1 ? 0 : (i / (datos.length - 1)) * (W - L - R));
  const y = (v: number) => T + (1 - v / tope) * (H - T - B);
  if (datos.every((d) => d.valor === 0)) return <p className="viz-vacio">Sin reportes en este rango.</p>;

  const linea = datos.map((d, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(d.valor).toFixed(1)}`).join(" ");
  const area = `${linea} L${x(datos.length - 1).toFixed(1)},${y(0)} L${x(0).toFixed(1)},${y(0)} Z`;
  const marcas = [0, tope / 2, tope];
  const ejeX = datos.length > 2 ? [0, Math.floor((datos.length - 1) / 2), datos.length - 1] : datos.map((_, i) => i);
  const etiqueta = (d: Par) => (granularidad === "semana" ? `Semana del ${fechaCorta(d.etiqueta)}` : fechaCorta(d.etiqueta));

  function mover(e: PointerEvent<SVGRectElement>) {
    const caja = e.currentTarget.getBoundingClientRect();
    const px = ((e.clientX - caja.left) / caja.width) * (W - L - R);
    setActivo(Math.max(0, Math.min(datos.length - 1, Math.round((px / (W - L - R)) * (datos.length - 1)))));
  }

  const a = activo !== null ? datos[activo] : null;
  return (
    <>
      <div className="serie" ref={caja}>
        <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`Reportes por ${granularidad === "semana" ? "semana" : "día"}`}>
          {marcas.map((m) => (
            <g key={m}>
              <line x1={L} x2={W - R} y1={y(m)} y2={y(m)} className="viz-grid" />
              <text x={L - 6} y={y(m) + 4} textAnchor="end" className="viz-eje">{m}</text>
            </g>
          ))}
          {ejeX.map((i) => (
            <text key={i} x={x(i)} y={H - 6} textAnchor={i === 0 ? "start" : i === datos.length - 1 ? "end" : "middle"} className="viz-eje">
              {fechaCorta(datos[i].etiqueta)}
            </text>
          ))}
          <path d={area} className="viz-area" />
          <path d={linea} className="viz-linea" />
          {a && <line x1={x(activo!)} x2={x(activo!)} y1={T} y2={H - B} className="viz-cruz" />}
          <circle cx={x(activo ?? datos.length - 1)} cy={y((a ?? datos[datos.length - 1]).valor)} r={5} className="viz-punto" />
          <rect x={L} y={T} width={W - L - R} height={H - T - B} fill="transparent"
            onPointerMove={mover} onPointerLeave={() => setActivo(null)} />
        </svg>
        {a && (
          <div className="viz-tip" style={{ left: `${(x(activo!) / W) * 100}%` }}>
            <strong>{a.valor}</strong> {a.valor === 1 ? "reporte" : "reportes"}
            <br />{etiqueta(a)}
          </div>
        )}
      </div>
      <VerTabla datos={datos} columna={granularidad === "semana" ? "Semana (inicio)" : "Día"} formato={fechaCorta} />
    </>
  );
}
