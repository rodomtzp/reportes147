import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./AuthContext";
import { CambiarPasswordPage } from "../features/auth/CambiarPasswordPage";
import { LoginPage } from "../features/auth/LoginPage";
import { CarrerasPage } from "../features/catalogos/CarrerasPage";
import { GruposPage } from "../features/catalogos/GruposPage";
import { PeriodosPage } from "../features/catalogos/PeriodosPage";
import { TiposIncidenciaPage } from "../features/catalogos/TiposIncidenciaPage";
import { TiposSancionPage } from "../features/catalogos/TiposSancionPage";
import { BitacoraPage } from "../features/exportaciones/BitacoraPage";
import { AvanceSemestrePage } from "../features/estudiantes/AvanceSemestrePage";
import { EstudianteDetallePage } from "../features/estudiantes/EstudianteDetallePage";
import { EstudianteFormPage } from "../features/estudiantes/EstudianteFormPage";
import { EstudiantesPage } from "../features/estudiantes/EstudiantesPage";
import { ImportarEstudiantesPage } from "../features/estudiantes/ImportarEstudiantesPage";
import { NuevoReportePage } from "../features/reportes/NuevoReportePage";
import { ReporteDetallePage } from "../features/reportes/ReporteDetallePage";
import { ReportesPage } from "../features/reportes/ReportesPage";
import { AlertasPage } from "../features/sanciones/AlertasPage";
import { ExpedientePage } from "../features/sanciones/ExpedientePage";
import { HomePage } from "../features/home/HomePage";
import { TutoresPage } from "../features/tutores/TutoresPage";
import { UsuariosPage } from "../features/usuarios/UsuariosPage";
import { Layout } from "../shared/components/Layout";
import { RutaProtegida } from "../shared/components/RutaProtegida";

const ADMIN = "ADMINISTRAR_CATALOGOS";

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/cambiar-password"
            element={<RutaProtegida permitirPasswordPendiente><CambiarPasswordPage /></RutaProtegida>}
          />
          <Route element={<RutaProtegida><Layout /></RutaProtegida>}>
            <Route path="/" element={<HomePage />} />
            <Route path="/reportes" element={<ReportesPage />} />
            <Route path="/reportes/nuevo" element={<RutaProtegida permiso="CREAR_REPORTE"><NuevoReportePage /></RutaProtegida>} />
            <Route path="/reportes/:id" element={<ReporteDetallePage />} />
            <Route path="/estudiantes" element={<EstudiantesPage />} />
            <Route path="/estudiantes/nuevo" element={<RutaProtegida permiso="GESTIONAR_ESTUDIANTES"><EstudianteFormPage /></RutaProtegida>} />
            <Route path="/estudiantes/:id" element={<EstudianteDetallePage />} />
            <Route path="/estudiantes/:id/expediente" element={<RutaProtegida permiso="VER_TODOS_LOS_REPORTES"><ExpedientePage /></RutaProtegida>} />
            <Route path="/alertas" element={<RutaProtegida permiso="VER_ALERTAS"><AlertasPage /></RutaProtegida>} />
            <Route path="/importar-estudiantes" element={<RutaProtegida permiso="IMPORTAR_ESTUDIANTES"><ImportarEstudiantesPage /></RutaProtegida>} />
            <Route path="/avance-semestre" element={<RutaProtegida permiso="AVANZAR_SEMESTRE"><AvanceSemestrePage /></RutaProtegida>} />
            <Route path="/bitacora" element={<RutaProtegida permiso="CONSULTAR_BITACORA"><BitacoraPage /></RutaProtegida>} />
            <Route path="/usuarios" element={<RutaProtegida permiso="GESTIONAR_USUARIOS"><UsuariosPage /></RutaProtegida>} />
            <Route path="/carreras" element={<RutaProtegida permiso={ADMIN}><CarrerasPage /></RutaProtegida>} />
            <Route path="/grupos" element={<RutaProtegida permiso={ADMIN}><GruposPage /></RutaProtegida>} />
            <Route path="/periodos" element={<RutaProtegida permiso={ADMIN}><PeriodosPage /></RutaProtegida>} />
            <Route path="/tutores" element={<RutaProtegida permiso={ADMIN}><TutoresPage /></RutaProtegida>} />
            <Route path="/tipos-incidencia" element={<RutaProtegida permiso={ADMIN}><TiposIncidenciaPage /></RutaProtegida>} />
            <Route path="/tipos-sancion" element={<RutaProtegida permiso={ADMIN}><TiposSancionPage /></RutaProtegida>} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
