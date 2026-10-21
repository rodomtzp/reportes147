"""Quién puede ver a qué estudiantes.

- Con GESTIONAR_ESTUDIANTES o VER_DATOS_CONTACTO (Administrador, Orientación, Subdirección,
  Dirección): todos.
- Tutor: solo los estudiantes inscritos hoy en los grupos que tutela en el periodo vigente.
- Cualquier otro: sin acceso a la ficha (solo el buscador con datos mínimos).
"""
from typing import Set

from app.domain.entities.usuario import Usuario
from app.domain.policies.politica_permisos import Permiso, tiene_permiso


def tiene_acceso_total(actor: Usuario) -> bool:
    return tiene_permiso(actor.roles, Permiso.VER_DATOS_CONTACTO) or tiene_permiso(
        actor.roles, Permiso.GESTIONAR_ESTUDIANTES
    )


def grupos_tutelados(uow, actor: Usuario) -> Set[int]:
    periodo = uow.periodos.obtener_vigente()
    if periodo is None:
        return set()
    return {a.grupo_id for a in uow.asignaciones_tutor.listar(periodo_id=periodo.id, usuario_id=actor.id)}
