"""Conversión de entidades y DTOs a diccionarios JSON (nunca se expone password_hash)."""


def usuario_a_dict(u) -> dict:
    return {
        "id": u.id,
        "nombre": u.nombre,
        "correo": u.correo,
        "roles": sorted(r.value for r in u.roles),
        "activo": u.activo,
        "debe_cambiar_password": u.debe_cambiar_password,
    }


def carrera_a_dict(c) -> dict:
    return {"id": c.id, "nombre": c.nombre, "clave": c.clave, "activa": c.activa}


def grupo_a_dict(g) -> dict:
    return {
        "id": g.id, "carrera_id": g.carrera_id, "semestre": g.semestre,
        "letra": g.letra, "clave": g.clave, "activo": g.activo,
    }


def periodo_a_dict(p) -> dict:
    return {
        "id": p.id, "nombre": p.nombre, "fecha_inicio": p.fecha_inicio.isoformat(),
        "fecha_fin": p.fecha_fin.isoformat(), "vigente": p.vigente,
    }


def tipo_incidencia_a_dict(t) -> dict:
    return {"id": t.id, "nombre": t.nombre, "activo": t.activo, "es_otro": t.es_otro}


def tipo_sancion_a_dict(t) -> dict:
    return {"id": t.id, "nombre": t.nombre, "requiere_dias": t.requiere_dias, "activo": t.activo}


def asignacion_a_dict(d) -> dict:
    a = d.asignacion
    return {
        "id": a.id, "usuario_id": a.usuario_id, "grupo_id": a.grupo_id, "periodo_id": a.periodo_id,
        "usuario_nombre": d.usuario_nombre, "grupo_clave": d.grupo_clave,
        "carrera_nombre": d.carrera_nombre, "periodo_nombre": d.periodo_nombre,
    }


# ---- Estudiantes ----
def estudiante_a_dict(e) -> dict:
    return {
        "id": e.id, "numero_control": e.numero_control, "primer_apellido": e.primer_apellido,
        "segundo_apellido": e.segundo_apellido, "nombres": e.nombres, "nombre_completo": e.nombre_completo,
        "telefono": e.telefono, "correo": e.correo, "calle": e.calle, "numero": e.numero,
        "colonia": e.colonia, "ciudad": e.ciudad, "generacion": e.generacion, "estatus": e.estatus.value,
    }


def estudiante_listado_a_dict(item) -> dict:
    e = item.estudiante
    return {
        "id": e.id, "numero_control": e.numero_control, "nombre_completo": e.nombre_completo,
        "telefono": e.telefono, "generacion": e.generacion, "estatus": e.estatus.value,
        "grupo": item.grupo_clave, "carrera": item.carrera_nombre,
    }


def estudiante_resumen_a_dict(r) -> dict:
    return {
        "id": r.id, "numero_control": r.numero_control, "nombre_completo": r.nombre_completo,
        "grupo": r.grupo_clave, "carrera": r.carrera_nombre,
    }


def tutor_legal_a_dict(t) -> dict:
    return {
        "id": t.id, "nombre": t.nombre, "parentesco": t.parentesco, "telefono": t.telefono,
        "correo": t.correo, "es_principal": t.es_principal,
    }


def estudiante_detalle_a_dict(d) -> dict:
    return {
        **estudiante_a_dict(d.estudiante),
        "grupo_actual": d.grupo_actual,
        "carrera_actual": d.carrera_actual,
        "tutores_legales": [tutor_legal_a_dict(t) for t in d.tutores_legales],
        "historial": [
            {"periodo": i.periodo_nombre, "grupo": i.grupo_clave, "semestre": i.semestre, "carrera": i.carrera_nombre}
            for i in d.inscripciones
        ],
    }


def importacion_a_dict(r) -> dict:
    fila = lambda f: {"fila": f.fila, "numero_control": f.numero_control, "motivo": f.motivo}  # noqa: E731
    return {"creados": r.creados, "omitidos": [fila(f) for f in r.omitidos], "errores": [fila(f) for f in r.errores]}


def avance_a_dict(r) -> dict:
    conteo: dict = {}
    for m in r.movimientos:
        conteo[m.accion] = conteo.get(m.accion, 0) + 1
    return {
        "ejecutado": r.ejecutado,
        "grupos_faltantes": r.grupos_faltantes,
        "omitidos_ya_inscritos": r.omitidos_ya_inscritos,
        "conteo": conteo,
        "movimientos": [
            {"estudiante_id": m.estudiante_id, "numero_control": m.numero_control, "nombre": m.nombre,
             "grupo_origen": m.grupo_origen, "grupo_destino": m.grupo_destino, "accion": m.accion}
            for m in r.movimientos
        ],
    }


# ---- Reportes ----
def _iso(valor):
    return valor.isoformat() if valor else None


def reporte_listado_a_dict(l) -> dict:
    r = l.reporte
    return {
        "id": r.id, "folio": r.folio, "incidente_id": r.incidente_id,
        "estudiante_id": r.estudiante_id, "estudiante": l.estudiante, "numero_control": l.numero_control,
        "grupo": l.grupo_clave, "carrera": l.carrera_nombre,
        "tipo_incidencia_id": r.tipo_incidencia_id, "tipo_incidencia": l.tipo_incidencia,
        "descripcion_otro": r.descripcion_otro,
        "resumen": r.descripcion if len(r.descripcion) <= 120 else r.descripcion[:117] + "…",
        "gravedad": r.gravedad.value, "estado": r.estado.value,
        "fecha_hora_incidente": _iso(r.fecha_hora_incidente), "creado_en": _iso(r.creado_en),
        "creado_por": l.creado_por_nombre, "cancelado": r.cancelado, "estado_llamada": l.estado_llamada,
    }


def adjunto_a_dict(a) -> dict:
    return {"id": a.id, "nombre": a.nombre_original, "tipo": a.tipo_mime, "tamano": a.tamano, "subido_en": _iso(a.subido_en)}


def evento_a_dict(e) -> dict:
    ev = e.evento
    return {
        "id": ev.id, "tipo": ev.tipo.value, "campo": ev.campo, "valor_anterior": ev.valor_anterior,
        "valor_nuevo": ev.valor_nuevo, "comentario": ev.comentario, "usuario": e.usuario_nombre, "fecha": _iso(ev.fecha),
    }


def reporte_detalle_a_dict(d) -> dict:
    r = d.listado.reporte
    return {
        **reporte_listado_a_dict(d.listado),
        "descripcion": r.descripcion,
        "motivo_cancelacion": r.motivo_cancelacion,
        "cancelado_por": d.cancelado_por_nombre,
        "cancelado_en": _iso(r.cancelado_en),
        "adjuntos": [adjunto_a_dict(a) for a in d.adjuntos],
        "llamadas": None if d.llamadas is None else [llamada_a_dict(l) for l in d.llamadas],
        "mensajes_whatsapp": None if d.mensajes is None else [mensaje_whatsapp_a_dict(m) for m in d.mensajes],
        "sancion": sancion_a_dict(d.sancion) if d.sancion else None,
        "acumulacion": acumulacion_a_dict(d.acumulacion) if d.acumulacion else None,
        "historial": [evento_a_dict(e) for e in d.historial],
        "relacionados": [
            {"id": x.reporte.id, "folio": x.reporte.folio, "estudiante": x.estudiante, "grupo": x.grupo_clave,
             "gravedad": x.reporte.gravedad.value, "cancelado": x.reporte.cancelado}
            for x in d.relacionados
        ],
    }


def reporte_creado_a_dict(c) -> dict:
    """Confirmación mínima: quien crea (p. ej. un prefecto) no necesariamente puede consultar reportes."""
    return {"id": c.reporte_id, "folio": c.folio, "estudiante": c.estudiante, "numero_control": c.numero_control}


# ---- Llamadas y WhatsApp ----
def llamada_a_dict(d) -> dict:
    i = d.intento
    return {
        "id": i.id, "estado": i.estado.value, "tutor_legal_id": i.tutor_legal_id, "tutor": d.tutor_nombre,
        "parentesco": d.tutor_parentesco, "atendio_nombre": i.atendio_nombre, "observaciones": i.observaciones,
        "fecha_hora": _iso(i.fecha_hora), "realizado_por": d.realizado_por_nombre,
    }


def mensaje_whatsapp_a_dict(d) -> dict:
    m = d.mensaje
    return {
        "id": m.id, "tutor_legal_id": m.tutor_legal_id, "tutor": d.tutor_nombre, "texto": m.texto,
        "generado_por": d.generado_por_nombre, "generado_en": _iso(m.generado_en), "enviado_en": _iso(m.enviado_en),
    }


def seguimiento_a_dict(s) -> dict:
    """Incluye teléfonos: solo para quien registra las llamadas."""
    return {
        "folio": s.folio, "estudiante": s.estudiante, "estado_llamada": s.estado_llamada,
        "tutores": [{**tutor_legal_a_dict(t)} for t in s.tutores],
        "llamadas": [llamada_a_dict(l) for l in s.llamadas],
        "mensajes": [mensaje_whatsapp_a_dict(m) for m in s.mensajes],
    }


def mensaje_generado_a_dict(g) -> dict:
    return {
        "id": g.mensaje.id, "texto": g.mensaje.texto, "enlace": g.enlace,
        "tutor": {"id": g.tutor.id, "nombre": g.tutor.nombre, "telefono": g.tutor.telefono},
    }


# ---- Sanciones, acumulación y alertas ----
def sancion_a_dict(d) -> dict:
    s = d.sancion
    return {
        "id": s.id, "origen": s.origen.value, "tipo": d.tipo_nombre, "tipo_sancion_id": s.tipo_sancion_id,
        "dias": s.dias, "observaciones": s.observaciones, "aplicada_por": d.aplicada_por_nombre,
        "aplicada_en": _iso(s.aplicada_en), "folios": d.folios,
    }


def acumulacion_a_dict(a) -> dict:
    return {"ciclo": a.ciclo_numero, "total": a.total, "umbral": a.umbral, "listo_para_sancion": a.listo_para_sancion}


def _ciclo_a_dict(c, umbral: int) -> dict:
    return {
        "numero": c.ciclo.numero, "abierto": c.ciclo.abierto, "fecha_inicio": _iso(c.ciclo.fecha_inicio),
        "fecha_cierre": _iso(c.ciclo.fecha_cierre), "contables": c.contables,
        "listo_para_sancion": c.ciclo.abierto and c.contables >= umbral,
        "reportes": [{**reporte_listado_a_dict(r), "cuenta": r.reporte.es_contable} for r in c.reportes],
        "sancion": sancion_a_dict(c.sancion) if c.sancion else None,
    }


def expediente_a_dict(e) -> dict:
    return {
        "estudiante_id": e.estudiante_id, "estudiante": e.estudiante, "numero_control": e.numero_control,
        "grupo_actual": e.grupo_actual, "total_reportes": e.total_reportes, "umbral": e.umbral,
        "ciclo_actual": _ciclo_a_dict(e.ciclo_actual, e.umbral) if e.ciclo_actual else None,
        "ciclos_anteriores": [_ciclo_a_dict(c, e.umbral) for c in e.ciclos_anteriores],
        "sanciones_directas": [sancion_a_dict(s) for s in e.sanciones_directas],
    }


def notificacion_a_dict(n) -> dict:
    return {
        "id": n.id, "tipo": n.tipo, "titulo": n.titulo, "mensaje": n.mensaje, "reporte_id": n.reporte_id,
        "estudiante_id": n.estudiante_id, "creada_en": _iso(n.creada_en), "correo_enviado": n.correo_enviado,
        "correo_error": n.correo_error, "atendida": n.atendida_en is not None, "atendida_en": _iso(n.atendida_en),
    }


def bitacora_a_dict(d) -> dict:
    r = d.registro
    return {
        "id": r.id, "accion": r.accion.value, "usuario_id": r.usuario_id, "usuario": d.usuario_nombre,
        "fecha": _iso(r.fecha), "descripcion": r.descripcion, "estudiante_id": r.estudiante_id,
        "estudiante": d.estudiante, "filas": r.filas, "con_contacto": r.con_contacto,
    }
