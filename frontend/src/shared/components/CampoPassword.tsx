import { useId, useState } from "react";

interface Props {
  etiqueta: string;
  valor: string;
  onCambio: (valor: string) => void;
  autoComplete: "current-password" | "new-password";
  ayuda?: string;
  minLength?: number;
  autoFocus?: boolean;
  invalido?: boolean;
}

/** Campo de contraseña con botón para mostrarla u ocultarla (útil en celular, donde es fácil equivocarse al teclear). */
export function CampoPassword({ etiqueta, valor, onCambio, autoComplete, ayuda, minLength, autoFocus, invalido }: Props) {
  const [visible, setVisible] = useState(false);
  const id = useId();
  return (
    <div className="campo">
      <label htmlFor={id}>{etiqueta}</label>
      <div className="campo-clave">
        <input id={id} type={visible ? "text" : "password"} value={valor} required minLength={minLength}
          autoComplete={autoComplete} autoFocus={autoFocus} aria-invalid={invalido || undefined}
          aria-describedby={ayuda ? `${id}-ayuda` : undefined} onChange={(e) => onCambio(e.target.value)} />
        <button type="button" className="ver-clave" aria-pressed={visible} onClick={() => setVisible(!visible)}>
          {visible ? "Ocultar" : "Mostrar"}
        </button>
      </div>
      {ayuda && <p className="ayuda" id={`${id}-ayuda`}>{ayuda}</p>}
    </div>
  );
}
