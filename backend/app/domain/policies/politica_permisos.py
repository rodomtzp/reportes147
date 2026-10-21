"""Matriz de permisos por rol (sección 3 de la especificación).

Es dominio puro: no depende de Flask ni de la base de datos.
Los permisos que dependen del grupo (Tutor) o de la autoría
(Docente: sus propios reportes) se resuelven en los casos de uso
de las fases siguientes, usando estos permisos como base.
"""
from enum import Enum
from typing import Iterable

from app.domain.value_objects.rol import Rol


class Permiso(str, Enum):
    CREAR_REPORTE = "CREAR_REPORTE"
    VER_REPORTES_PROPIOS = "VER_REPORTES_PROPIOS"
    VER_TODOS_LOS_REPORTES = "VER_TODOS_LOS_REPORTES"
    CORREGIR_REPORTE = "CORREGIR_REPORTE"
    CAMBIAR_GRAVEDAD = "CAMBIAR_GRAVEDAD"
    REGISTRAR_LLAMADAS = "REGISTRAR_LLAMADAS"
    TURNAR_A_SUBDIRECCION = "TURNAR_A_SUBDIRECCION"
    APLICAR_SANCIONES = "APLICAR_SANCIONES"
    VER_ALERTAS = "VER_ALERTAS"
    CANCELAR_REPORTE = "CANCELAR_REPORTE"
    VER_DATOS_CONTACTO = "VER_DATOS_CONTACTO"
    EXPORTAR_EXCEL = "EXPORTAR_EXCEL"
    GESTIONAR_ESTUDIANTES = "GESTIONAR_ESTUDIANTES"
    IMPORTAR_ESTUDIANTES = "IMPORTAR_ESTUDIANTES"
    AVANZAR_SEMESTRE = "AVANZAR_SEMESTRE"
    ADMINISTRAR_CATALOGOS = "ADMINISTRAR_CATALOGOS"
    GESTIONAR_USUARIOS = "GESTIONAR_USUARIOS"
    CONSULTAR_BITACORA = "CONSULTAR_BITACORA"


P = Permiso

_DIRECTIVO_BASE = {
    P.CREAR_REPORTE,
    P.VER_TODOS_LOS_REPORTES,
    P.CORREGIR_REPORTE,
    P.CAMBIAR_GRAVEDAD,
    P.CANCELAR_REPORTE,
    P.VER_DATOS_CONTACTO,
    P.EXPORTAR_EXCEL,
}

PERMISOS_POR_ROL = {
    Rol.DOCENTE: {P.CREAR_REPORTE, P.VER_REPORTES_PROPIOS, P.EXPORTAR_EXCEL},
    Rol.PREFECTO: {P.CREAR_REPORTE},  # solo genera, no consulta
    Rol.ORIENTACION: _DIRECTIVO_BASE | {P.REGISTRAR_LLAMADAS, P.TURNAR_A_SUBDIRECCION, P.GESTIONAR_ESTUDIANTES},
    Rol.SUBDIRECCION: _DIRECTIVO_BASE | {P.APLICAR_SANCIONES, P.GESTIONAR_ESTUDIANTES, P.VER_ALERTAS},
    Rol.DIRECCION: _DIRECTIVO_BASE | {P.APLICAR_SANCIONES, P.VER_ALERTAS},
    Rol.ADMINISTRADOR: {
        P.GESTIONAR_ESTUDIANTES,
        P.IMPORTAR_ESTUDIANTES,
        P.AVANZAR_SEMESTRE,
        P.ADMINISTRAR_CATALOGOS,
        P.GESTIONAR_USUARIOS,
        P.CONSULTAR_BITACORA,
    },
}


def permisos_de(roles: Iterable[Rol]) -> frozenset:
    """Unión de permisos de todos los roles del usuario."""
    resultado = set()
    for rol in roles:
        resultado |= PERMISOS_POR_ROL.get(Rol(rol), set())
    return frozenset(resultado)


def tiene_permiso(roles: Iterable[Rol], permiso: Permiso) -> bool:
    return permiso in permisos_de(roles)
