"""Implementaciones en memoria de los puertos, para probar casos de uso sin base de datos.

Se guardan y devuelven copias para imitar el comportamiento real: lo que un caso de uso
modifica y no guarda (o lo que se descarta por un error) no altera el almacén.
"""
from copy import deepcopy

from app.application.ports.repositorios import (
    AdjuntoRepositorio, AsignacionTutorRepositorio, BitacoraRepositorio, CarreraRepositorio, CicloRepositorio, EstudianteRepositorio, GrupoRepositorio,
    HistorialReporteRepositorio, InscripcionRepositorio, LlamadaRepositorio, MensajeWhatsAppRepositorio,
    NotificacionRepositorio, PeriodoRepositorio, ReporteRepositorio, SancionRepositorio, TipoIncidenciaRepositorio, TipoSancionRepositorio,
    TutorLegalRepositorio, UsuarioRepositorio,
)
from app.application.ports.almacen_archivos import AlmacenArchivosPuerto
from app.application.ports.correo import CorreoPuerto
from app.application.ports.notificador import NotificadorPuerto
from app.application.ports.reloj import RelojPuerto
from app.application.ports.seguridad import HasherPuerto
from app.application.ports.unidad_de_trabajo import UnidadDeTrabajo


class _Base:
    def __init__(self):
        self._items = {}
        self._sig = 1

    def obtener_por_id(self, id_):
        e = self._items.get(id_)
        return deepcopy(e) if e else None

    def guardar(self, e):
        if e.id is None:
            e.id = self._sig
            self._sig += 1
        self._items[e.id] = deepcopy(e)
        return e

    def _todos(self):
        return [deepcopy(e) for e in self._items.values()]

    def _buscar(self, pred):
        return next((deepcopy(e) for e in self._items.values() if pred(e)), None)


class UsuarioRepoMem(_Base, UsuarioRepositorio):
    def obtener_por_ids(self, ids):
        return {i: deepcopy(self._items[i]) for i in ids if i in self._items}

    def obtener_por_correo(self, correo):
        return self._buscar(lambda u: u.correo == correo.strip().lower())

    def listar(self, rol=None, activo=None):
        return sorted(
            (u for u in self._todos()
             if (rol is None or rol in u.roles) and (activo is None or u.activo == activo)),
            key=lambda u: u.nombre,
        )


class CarreraRepoMem(_Base, CarreraRepositorio):
    def obtener_por_clave(self, clave):
        return self._buscar(lambda c: c.clave == clave.strip().upper())

    def listar(self, solo_activas=False):
        return [c for c in self._todos() if c.activa or not solo_activas]


class GrupoRepoMem(_Base, GrupoRepositorio):
    def obtener_por_semestre_y_letra(self, semestre, letra):
        return self._buscar(lambda g: g.semestre == semestre and g.letra == letra.strip().upper())

    def listar(self, carrera_id=None, semestre=None, solo_activos=False):
        return [
            g for g in self._todos()
            if (carrera_id is None or g.carrera_id == carrera_id)
            and (semestre is None or g.semestre == semestre)
            and (g.activo or not solo_activos)
        ]


class PeriodoRepoMem(_Base, PeriodoRepositorio):
    def obtener_por_nombre(self, nombre):
        return self._buscar(lambda p: p.nombre == nombre.strip())

    def obtener_vigente(self):
        return self._buscar(lambda p: p.vigente)

    def listar(self):
        return self._todos()

    def desactivar_vigentes(self):
        for p in self._items.values():
            p.vigente = False


class TipoIncidenciaRepoMem(_Base, TipoIncidenciaRepositorio):
    def obtener_por_nombre(self, nombre):
        return self._buscar(lambda t: t.nombre.lower() == nombre.strip().lower())

    def listar(self, solo_activos=False):
        return [t for t in self._todos() if t.activo or not solo_activos]


class TipoSancionRepoMem(_Base, TipoSancionRepositorio):
    def obtener_por_nombre(self, nombre):
        return self._buscar(lambda t: t.nombre.lower() == nombre.strip().lower())

    def listar(self, solo_activos=False):
        return [t for t in self._todos() if t.activo or not solo_activos]


class AsignacionRepoMem(_Base, AsignacionTutorRepositorio):
    def obtener_por_grupo_y_periodo(self, grupo_id, periodo_id):
        return self._buscar(lambda a: a.grupo_id == grupo_id and a.periodo_id == periodo_id)

    def listar(self, periodo_id=None, grupo_id=None, usuario_id=None):
        return [
            a for a in self._todos()
            if (periodo_id is None or a.periodo_id == periodo_id)
            and (grupo_id is None or a.grupo_id == grupo_id)
            and (usuario_id is None or a.usuario_id == usuario_id)
        ]

    def eliminar(self, asignacion_id):
        self._items.pop(asignacion_id, None)


class InscripcionRepoMem(_Base, InscripcionRepositorio):
    def obtener_por_ids(self, ids):
        return {i: deepcopy(self._items[i]) for i in ids if i in self._items}

    def __init__(self, periodos):
        super().__init__()
        self._periodos = periodos

    def obtener(self, estudiante_id, periodo_id):
        return self._buscar(lambda i: i.estudiante_id == estudiante_id and i.periodo_id == periodo_id)

    def obtener_de_estudiantes(self, ids, periodo_id):
        ids = set(ids)
        return {i.estudiante_id: i for i in self._todos() if i.estudiante_id in ids and i.periodo_id == periodo_id}

    def listar_por_estudiante(self, estudiante_id):
        propias = [i for i in self._todos() if i.estudiante_id == estudiante_id]
        return sorted(propias, key=lambda i: self._periodos.obtener_por_id(i.periodo_id).fecha_inicio)

    def listar_por_periodo(self, periodo_id):
        return [i for i in self._todos() if i.periodo_id == periodo_id]


class TutorLegalRepoMem(_Base, TutorLegalRepositorio):
    def listar_por_estudiante(self, estudiante_id):
        propios = [t for t in self._todos() if t.estudiante_id == estudiante_id]
        return sorted(propios, key=lambda t: (not t.es_principal, t.id))

    def eliminar(self, tutor_id):
        self._items.pop(tutor_id, None)


class EstudianteRepoMem(_Base, EstudianteRepositorio):
    def __init__(self, inscripciones, grupos):
        super().__init__()
        self._insc = inscripciones
        self._grupos = grupos

    def obtener_por_ids(self, ids):
        return {i: deepcopy(self._items[i]) for i in ids if i in self._items}

    def obtener_por_numero_control(self, numero_control):
        return self._buscar(lambda e: e.numero_control == numero_control.strip().upper())

    @staticmethod
    def _coincide(e, texto):
        campos = " ".join(filter(None, [e.numero_control, e.primer_apellido, e.segundo_apellido, e.nombres])).lower()
        return all(t.lower() in campos for t in (texto or "").split())

    def listar(self, texto=None, estatus=None, grupo_ids=None, carrera_id=None, periodo_id=None, limite=200, offset=0):
        resultado = []
        for e in self._todos():
            if not self._coincide(e, texto) or (estatus is not None and e.estatus != estatus):
                continue
            if grupo_ids is not None or carrera_id is not None:
                insc = self._insc.obtener(e.id, periodo_id)
                if insc is None:
                    continue
                if grupo_ids is not None and insc.grupo_id not in grupo_ids:
                    continue
                if carrera_id is not None and self._grupos.obtener_por_id(insc.grupo_id).carrera_id != carrera_id:
                    continue
            resultado.append(e)
        resultado.sort(key=lambda e: (e.primer_apellido, e.segundo_apellido or "", e.nombres))
        return resultado[offset:offset + limite]

    def buscar_activos(self, texto, limite=15):
        from app.domain.value_objects.estatus_estudiante import EstatusEstudiante
        return self.listar(texto=texto, estatus=EstatusEstudiante.ACTIVO, limite=limite)


class LlamadaRepoMem(_Base, LlamadaRepositorio):
    def obtener_pendiente(self, reporte_id):
        return next((i for i in self.listar_por_reporte(reporte_id) if i.estado.value == "PENDIENTE"), None)

    def listar_por_reporte(self, reporte_id):
        return sorted((i for i in self._todos() if i.reporte_id == reporte_id), key=lambda i: i.id)

    def listar_por_reportes(self, reporte_ids):
        ids, salida = set(reporte_ids), {}
        for i in sorted(self._todos(), key=lambda i: i.id):
            if i.reporte_id in ids:
                salida.setdefault(i.reporte_id, []).append(i)
        return salida

    def tutor_tiene_resultados(self, tutor_id):
        return any(i.tutor_legal_id == tutor_id and i.estado.value != "PENDIENTE" for i in self._items.values())

    def reasignar_pendientes(self, tutor_id, nuevo_tutor_id):
        for i in self._items.values():
            if i.tutor_legal_id == tutor_id and i.estado.value == "PENDIENTE":
                i.tutor_legal_id = nuevo_tutor_id


class MensajeRepoMem(_Base, MensajeWhatsAppRepositorio):
    def listar_por_reporte(self, reporte_id):
        return sorted((m for m in self._todos() if m.reporte_id == reporte_id), key=lambda m: m.id)

    def tutor_tiene_mensajes(self, tutor_id):
        return any(m.tutor_legal_id == tutor_id for m in self._items.values())


class CicloRepoMem(_Base, CicloRepositorio):
    def obtener_abierto(self, estudiante_id):
        return self._buscar(lambda c: c.estudiante_id == estudiante_id and c.abierto)

    def listar_por_estudiante(self, estudiante_id):
        return sorted((c for c in self._todos() if c.estudiante_id == estudiante_id), key=lambda c: c.numero)

    def siguiente_numero(self, estudiante_id):
        return max([c.numero for c in self.listar_por_estudiante(estudiante_id)] or [0]) + 1


class SancionRepoMem(_Base, SancionRepositorio):
    def obtener_por_reporte(self, reporte_id):
        return self._buscar(lambda s: s.reporte_id == reporte_id)

    def obtener_por_ciclo(self, ciclo_id):
        return self._buscar(lambda s: s.ciclo_id == ciclo_id)

    def listar_por_estudiante(self, estudiante_id):
        return sorted((s for s in self._todos() if s.estudiante_id == estudiante_id), key=lambda s: s.id, reverse=True)


class NotificacionRepoMem(_Base, NotificacionRepositorio):
    def listar(self, rol_destino, solo_pendientes=False, limite=100, offset=0):
        todas = [n for n in self._todos() if n.rol_destino == rol_destino and (n.atendida_en is None or not solo_pendientes)]
        return sorted(todas, key=lambda n: n.id, reverse=True)[offset:offset + limite]

    def contar_pendientes(self, rol_destino):
        return sum(1 for n in self._items.values() if n.rol_destino == rol_destino and n.atendida_en is None)


class BitacoraRepoMem(_Base, BitacoraRepositorio):
    def agregar(self, registro):
        return self.guardar(registro)

    def listar(self, accion=None, usuario_id=None, estudiante_id=None, desde=None, hasta=None, limite=100, offset=0):
        r = [x for x in self._todos()
             if (accion is None or x.accion == accion) and (usuario_id is None or x.usuario_id == usuario_id)
             and (estudiante_id is None or x.estudiante_id == estudiante_id)
             and (desde is None or x.fecha >= desde) and (hasta is None or x.fecha <= hasta)]
        return sorted(r, key=lambda x: (x.fecha, x.id), reverse=True)[offset:offset + limite]


class ReporteRepoMem(_Base, ReporteRepositorio):
    def __init__(self, inscripciones, estudiantes, grupos, llamadas):
        super().__init__()
        self._insc, self._est, self._grupos, self._llamadas = inscripciones, estudiantes, grupos, llamadas
        self._folios = {}

    def siguiente_numero_folio(self, anio):
        self._folios[anio] = self._folios.get(anio, 0) + 1
        return self._folios[anio]

    def listar(self, f):
        a, salida = f.acceso, []
        for r in self._todos():
            if not a.total:
                ok = a.creador_id is not None and r.creado_por == a.creador_id
                if not ok and a.grupo_ids and a.periodo_id is not None:
                    insc = self._insc.obtener(r.estudiante_id, a.periodo_id)
                    ok = insc is not None and insc.grupo_id in a.grupo_ids
                if not ok:
                    continue
            if f.reporte_id is not None and r.id != f.reporte_id: continue
            if f.incidente_id is not None and r.incidente_id != f.incidente_id: continue
            if f.estudiante_id is not None and r.estudiante_id != f.estudiante_id: continue
            if f.estado is not None and r.estado != f.estado: continue
            if f.gravedad is not None and r.gravedad != f.gravedad: continue
            if f.tipo_incidencia_id is not None and r.tipo_incidencia_id != f.tipo_incidencia_id: continue
            if f.desde is not None and r.fecha_hora_incidente < f.desde: continue
            if f.hasta is not None and r.fecha_hora_incidente > f.hasta: continue
            if r.cancelado and not f.incluir_cancelados: continue
            if f.ciclo_id is not None and r.ciclo_id != f.ciclo_id: continue
            if f.solo_contables and not r.es_contable: continue
            if f.sin_llamada_efectiva and any(i.es_efectiva for i in self._llamadas.listar_por_reporte(r.id)): continue
            if f.grupo_id is not None or f.carrera_id is not None:
                g = self._grupos.obtener_por_id(self._insc.obtener_por_ids([r.inscripcion_id])[r.inscripcion_id].grupo_id)
                if f.grupo_id is not None and g.id != f.grupo_id: continue
                if f.carrera_id is not None and g.carrera_id != f.carrera_id: continue
            if f.texto:
                e = self._est.obtener_por_id(r.estudiante_id)
                pajar = " ".join(filter(None, [r.folio, e.numero_control, e.primer_apellido, e.segundo_apellido, e.nombres])).lower()
                if not all(t.lower() in pajar for t in f.texto.split()): continue
            salida.append(r)
        salida.sort(key=lambda r: (r.fecha_hora_incidente, r.id), reverse=True)
        return salida[f.offset:f.offset + f.limite]

    def es_visible(self, reporte_id, acceso):
        from app.application.dto.reportes import FiltroReportes
        return bool(self.listar(FiltroReportes(acceso=acceso, reporte_id=reporte_id, incluir_cancelados=True, limite=1)))


class HistorialRepoMem(_Base, HistorialReporteRepositorio):
    def agregar(self, evento):
        return self.guardar(evento)

    def listar_por_reporte(self, reporte_id):
        return sorted((e for e in self._todos() if e.reporte_id == reporte_id), key=lambda e: e.id)


class AdjuntoRepoMem(_Base, AdjuntoRepositorio):
    def listar_por_reporte(self, reporte_id):
        return sorted((a for a in self._todos() if a.reporte_id == reporte_id), key=lambda a: a.id)


class UoWMem(UnidadDeTrabajo):
    def __init__(self):
        self.usuarios = UsuarioRepoMem()
        self.carreras = CarreraRepoMem()
        self.grupos = GrupoRepoMem()
        self.periodos = PeriodoRepoMem()
        self.tipos_incidencia = TipoIncidenciaRepoMem()
        self.tipos_sancion = TipoSancionRepoMem()
        self.asignaciones_tutor = AsignacionRepoMem()
        self.inscripciones = InscripcionRepoMem(self.periodos)
        self.tutores_legales = TutorLegalRepoMem()
        self.estudiantes = EstudianteRepoMem(self.inscripciones, self.grupos)
        self.llamadas = LlamadaRepoMem()
        self.ciclos = CicloRepoMem()
        self.sanciones = SancionRepoMem()
        self.notificaciones = NotificacionRepoMem()
        self.bitacora = BitacoraRepoMem()
        self.mensajes_whatsapp = MensajeRepoMem()
        self.reportes = ReporteRepoMem(self.inscripciones, self.estudiantes, self.grupos, self.llamadas)
        self.historial_reportes = HistorialRepoMem()
        self.adjuntos = AdjuntoRepoMem()
        self.commits = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return None

    def commit(self):
        self.commits += 1

    def rollback(self):
        pass


class HasherFalso(HasherPuerto):
    def hashear(self, password: str) -> str:
        return "hash:" + password

    def verificar(self, password: str, password_hash: str) -> bool:
        return password_hash == "hash:" + password


class RelojFalso(RelojPuerto):
    def __init__(self, ahora):
        self._ahora = ahora

    def ahora(self):
        return self._ahora

    def avanzar(self, **kw):
        self._ahora = self._ahora + __import__("datetime").timedelta(**kw)

    def fijar(self, valor):
        self._ahora = valor

    def localizar(self, valor):
        return valor.replace(tzinfo=self._ahora.tzinfo) if valor.tzinfo is None else valor.astimezone(self._ahora.tzinfo)


class AlmacenMem(AlmacenArchivosPuerto):
    def __init__(self):
        self.archivos = {}

    def guardar(self, contenido, extension):
        clave = f"{len(self.archivos) + 1}{extension}"
        self.archivos[clave] = contenido
        return clave

    def leer(self, clave):
        return self.archivos[clave]


class NotificadorMem(NotificadorPuerto):
    def __init__(self):
        self.alertas, self.acumulaciones, self.falla = [], [], False

    def alertar_gravedad_a_subdireccion(self, alertas):
        if self.falla:
            raise RuntimeError("SMTP caído")
        self.alertas.extend(alertas)

    def alertar_acumulacion_a_subdireccion(self, alertas):
        if self.falla:
            raise RuntimeError("SMTP caído")
        self.acumulaciones.extend(alertas)


class CorreoMem(CorreoPuerto):
    def __init__(self):
        self.enviados, self.falla = [], None

    def enviar(self, destinatarios, asunto, cuerpo):
        if self.falla:
            raise RuntimeError(self.falla)
        self.enviados.append((list(destinatarios), asunto, cuerpo))
