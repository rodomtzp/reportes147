# Sistema de Control de Reportes – CBTis 147

Flask + SQLAlchemy + PostgreSQL (backend) y React + TypeScript (frontend), con Clean Architecture.
Estado actual: **Fase 6 — versión 1.0** (exportaciones a Excel, bitácora, seguridad, respaldos y despliegue) sobre la Fase 5 (sanciones, ciclos de acumulación y alertas), la Fase 4 (llamadas y WhatsApp), la Fase 3 (reportes), la Fase 2 (estudiantes, importación y avance de semestre), la Fase 1 (catálogos, usuarios y tutores) y la Fase 0 (fundamentos y autenticación).

## Aplicación en línea de ejemplo

- URL: https://reportes-web-hvrr.onrender.com/login
- API: https://reportes-api-zowi.onrender.com/api/v1/health
- VIDEO:


## Arranque rápido (Docker)

```bash
cp .env.example .env          # y cambia SECRET_KEY y POSTGRES_PASSWORD
docker compose -f docker-compose.dev.yml up --build   # desarrollo con recarga en caliente
```

- API: http://localhost:5000/api/v1/health
- PostgreSQL expuesto en el puerto **5433** del equipo (por si ya tienes uno en el 5432)
- Frontend: http://localhost:5173

Las migraciones se aplican solas al iniciar el backend. Crea el primer administrador:

```bash
docker compose -f docker-compose.dev.yml exec backend python -m app.cli crear-usuario \
  --nombre "Administrador" --correo admin@cbtis147.edu.mx --roles ADMINISTRADOR
```

(Pide la contraseña de forma interactiva; mínimo 10 caracteres.)

## Pruebas del backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest
```

- `tests/unit`: dominio y casos de uso, sin base de datos.
- `tests/integration`: API completa sobre SQLite en memoria.

## Nueva migración

```bash
docker compose -f docker-compose.dev.yml exec backend alembic revision --autogenerate -m "descripcion"
docker compose -f docker-compose.dev.yml exec backend alembic upgrade head
```

## Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| GET | /api/v1/health | Estado de la API y la base de datos |
| POST | /api/v1/auth/login | `{correo, password}` → access y refresh token |
| POST | /api/v1/auth/refresh | `{refresh_token}` → nuevo access token |
| GET | /api/v1/auth/me | Usuario, roles, permisos y si debe cambiar su contraseña |
| POST | /api/v1/auth/cambiar-password | `{password_actual, password_nueva}` |

### Fase 1 (lectura: cualquier usuario autenticado · escritura: Administrador)

| Recurso | Rutas |
|---|---|
| Usuarios (solo Administrador) | `GET/POST /usuarios`, `PATCH /usuarios/{id}`, `POST /usuarios/{id}/restablecer-password` |
| Carreras | `GET/POST /carreras`, `PATCH /carreras/{id}` |
| Grupos | `GET/POST /grupos`, `PATCH /grupos/{id}` (clave = semestre + letra, ej. 1G) |
| Periodos | `GET/POST /periodos`, `PATCH /periodos/{id}`, `POST /periodos/{id}/vigente` |
| Tutores (solo Administrador) | `GET/POST /asignaciones-tutor`, `DELETE /asignaciones-tutor/{id}` |
| Tipos de incidencia | `GET/POST /tipos-incidencia`, `PATCH /tipos-incidencia/{id}` |
| Tipos de sanción | `GET/POST /tipos-sancion`, `PATCH /tipos-sancion/{id}` |

Las migraciones `0002` y `0003` crean las tablas y siembran los catálogos iniciales
(incidencias con la opción "Otro", y sanciones: suspensión de N días, carta compromiso, servicio comunitario).

**Altas de usuarios:** el administrador crea el usuario y el sistema genera una contraseña temporal que se
muestra una sola vez. Con ella el usuario solo puede cambiar su contraseña; el resto de la API responde 403
(`CAMBIO_PASSWORD_REQUERIDO`) hasta que lo haga.

**Reglas destacadas:** un grupo (semestre + letra) pertenece a una sola carrera; solo un periodo puede estar
vigente; un grupo tiene un solo tutor por periodo y el tutor debe ser docente; la opción "Otro" no se
renombra ni se desactiva; el administrador no puede desactivarse ni quitarse su propio rol.

### Fase 2: estudiantes

| Método | Ruta | Quién |
|---|---|---|
| GET | `/estudiantes/buscar?q=` | Quien puede crear reportes. Devuelve solo control, nombre, grupo y carrera (sin teléfonos ni dirección) |
| GET | `/estudiantes`, `/estudiantes/{id}` | Administrador, Orientación, Subdirección y Dirección: todos. Tutor: solo su(s) grupo(s) del periodo vigente |
| POST/PATCH | `/estudiantes`, `/estudiantes/{id}` | Administrador, Orientación, Subdirección |
| POST | `/estudiantes/{id}/grupo` | Corrige el grupo del periodo vigente |
| POST/PATCH/DELETE | `/estudiantes/{id}/tutores-legales`, `/tutores-legales/{id}` | Padres o tutores (siempre uno principal; mínimo uno) |
| GET | `/estudiantes/plantilla` | Administrador: descarga el CSV de ejemplo |
| POST | `/estudiantes/importar` | Administrador: `multipart/form-data`, campo `archivo` (.csv o .xlsx) |
| POST | `/estudiantes/avance-semestre` | Administrador: `{periodo_origen_id, periodo_destino_id, excepciones, simular}` |

**Historial:** cada estudiante tiene una *inscripción* por periodo (grupo + periodo). Un reporte futuro quedará
ligado a la inscripción vigente, de modo que el historial conserva el grupo correcto aunque el estudiante cambie de semestre.

**Importación** (la fila 1 es el encabezado): obligatorias `numero_control, primer_apellido, nombres, generacion,
grupo, tutor_nombre, tutor_telefono`; opcionales `segundo_apellido, telefono, correo, calle, numero, colonia, ciudad,
tutor_parentesco, tutor_correo`. Los estudiantes nuevos se crean e inscriben en su grupo del periodo vigente; los que ya
existen o se repiten se **omiten y se reportan**; las filas inválidas se reportan como error sin frenar al resto.
Teléfonos: 10 dígitos (acepta espacios, guiones y +52).

**Avance de semestre:** cada estudiante activo pasa al grupo del semestre siguiente conservando la letra (1G → 2G);
sexto semestre egresa. Excepciones: `REPETIR` y `BAJA`. Con `simular: true` (valor por defecto) solo devuelve la
vista previa; es idempotente y falla sin guardar nada si faltan grupos del semestre siguiente. Después hay que marcar
el periodo nuevo como vigente.

### Fase 3: reportes

| Método | Ruta | Quién |
|---|---|---|
| POST | `/reportes` | Quien puede crear reportes. Un reporte **por estudiante** (varios estudiantes → varios reportes ligados por `incidente_id`) |
| GET | `/reportes` (filtros: `estudiante_id, grupo_id, carrera_id, estado, gravedad, tipo_incidencia_id, desde, hasta, q, incluir_cancelados, limite, offset`) | Según rol |
| GET | `/reportes/{id}` | Detalle con historial, evidencias y reportes relacionados |
| PATCH | `/reportes/{id}` | Orientación, Subdirección, Dirección: corregir tipo, descripción o fecha |
| POST | `/reportes/{id}/gravedad` | Cambiar gravedad (con motivo) |
| POST | `/reportes/{id}/turnar` | Orientación: pasa a "Atendido por Subdirección" |
| POST | `/reportes/{id}/cancelar` | Cancelar con motivo (los reportes nunca se borran) |
| POST | `/reportes/{id}/adjuntos` | `multipart`: `archivo` y `aplicar_a_incidente` |
| GET | `/reportes/{id}/adjuntos/{adjunto_id}` | Descarga protegida |

**Folio:** `RPT-AAAA-NNNN`, consecutivo que se reinicia cada año (contador con bloqueo de fila; la migración precarga 2026–2040).

**Flujo:** el reporte nace ya en *En revisión por Orientación*. Los **Grave** y **Muy grave** además alertan a
Subdirección al crearse o al escalarse (no cada vez que se modifican dentro de esas gravedades). Hoy la alerta queda en
el log del servidor; la bandeja interna y el correo llegan en la Fase 5 sin modificar los casos de uso.

**Quién ve qué:** Orientación, Subdirección y Dirección ven todos; el **tutor**, todo el historial de los estudiantes de sus
grupos del periodo vigente; el **docente**, los que él creó; el **prefecto** solo genera (la respuesta de creación solo
trae folio y nombre). Los reportes relacionados de un incidente solo muestran los que el usuario puede ver.

**Quién corrige:** solo Orientación, Subdirección y Dirección; cada cambio queda en `historial_reportes`
(estado, gravedad, correcciones campo por campo, cancelación y evidencias).

**Evidencias:** JPG, PNG, WEBP o PDF (el tipo se valida por su contenido, no por la extensión), máx. 5 MB y 5 por reporte.
Se guardan con nombre aleatorio en el volumen `uploads` (`/data/uploads`) y se descargan siempre como adjunto con
`nosniff`. El autor puede agregar evidencias mientras el reporte esté en revisión; Orientación, Subdirección y Dirección
hasta que se concluya. Incluye el volumen `uploads` en tus respaldos.

### Fase 4: llamadas a padres y WhatsApp

| Método | Ruta | Quién |
|---|---|---|
| GET | `/reportes/{id}/llamadas` | Orientación: tutores (con teléfono), intentos y mensajes |
| POST | `/reportes/{id}/llamadas` | Orientación: `{estado, tutor_legal_id?, atendio_nombre?, observaciones?, fecha_hora?}` |
| POST | `/reportes/{id}/whatsapp` | Orientación: genera el texto formal y el enlace `wa.me` |
| POST | `/mensajes-whatsapp/{id}/enviado` | Orientación: confirma que el mensaje se envió |
| GET | `/reportes?sin_llamada_efectiva=true` | Reportes sin ninguna llamada Realizada o Atendida |

**Regla:** cada reporte genera una llamada **Pendiente** al padre o tutor principal (incluso si varios reportes son del
mismo incidente). Orientación registra el resultado —*Realizada*, *No contestó* o *Atendida* (con quién atendió)— y puede
elegir a otro tutor en cada intento. Tras un “No contestó” se registran nuevos intentos; todos quedan guardados y en el
historial del reporte. El reporte solo podrá concluirse (Fase 5) con al menos una llamada Realizada o Atendida.

**WhatsApp:** por ahora el sistema genera el mensaje formal (estudiante, grupo, folio, tipo de incidencia, fecha e invitación
a comunicarse con Orientación; **sin** la descripción de los hechos ni la gravedad) y un enlace `https://wa.me/52…`
que Orientación abre para enviarlo desde su WhatsApp; luego pulsa “Ya lo envié”. Todo mensaje generado queda registrado.
La integración está detrás del puerto `MensajeriaPuerto`, así que conectar la API de WhatsApp Business más adelante solo
requiere una implementación nueva. Variables opcionales: `PLANTEL_NOMBRE`, `ORIENTACION_CONTACTO` (texto al final del
mensaje, p. ej. teléfono y horario) y `WHATSAPP_CODIGO_PAIS` (52 por defecto).

**Privacidad:** los teléfonos solo se devuelven a Orientación; Subdirección y Dirección ven el historial de llamadas sin
teléfonos; el docente autor y el tutor ven únicamente el resumen (Pendiente / No contestó / Realizada / Atendida).
Un padre o tutor con llamadas o mensajes registrados no puede eliminarse.

### Fase 5: sanciones, acumulación y alertas

| Método | Ruta | Quién |
|---|---|---|
| POST | `/reportes/{id}/sancion` | Subdirección, Dirección: sanción **directa** (`{tipo_sancion_id, dias?, observaciones?}`) |
| POST | `/estudiantes/{id}/sancion-acumulacion` | Subdirección, Dirección: sanción por **acumulación** del ciclo |
| GET | `/estudiantes/{id}/expediente` | Orientación, Subdirección, Dirección: ciclos, reportes que cuentan y sanciones de toda su carrera |
| GET | `/alertas` (`?pendientes=false` para todas), `/alertas/resumen` | Subdirección y Dirección: bandeja |
| POST | `/alertas/{id}/atendida` | Marcar una alerta como vista |

**Ciclo de acumulación.** Cada estudiante tiene un ciclo abierto; todos sus reportes nuevos entran a él. Cuentan para las
3 faltas los reportes **no cancelados y sin sanción directa** (los Leves ya atendidos sin sanción siguen contando, y un
Grave sin sanción directa también). Al llegar a 3 o más, Subdirección o Dirección aplican **una sola sanción** que cubre
todos los reportes del ciclo, los pasa a *Sancionado / Concluido*, cierra el ciclo y el contador vuelve a cero (el siguiente
reporte abre el ciclo 2). Siempre se cierra con una sanción: se elige el tipo (y los días si el tipo los requiere).

**Sanción directa.** Solo para reportes **Grave** o **Muy grave**: el reporte pasa a *Sancionado / Concluido* (si aún estaba
en Orientación, pasa antes por *Atendido por Subdirección*, con historial), **deja de contar** para las 3 faltas y **no
cierra ni reinicia** el ciclo.

**Condición para concluir.** Ningún reporte se concluye sin al menos una llamada *Realizada* o *Atendida*. En una sanción
por acumulación, si falta en alguno, el mensaje lista los folios y no se guarda nada (la operación es atómica).

**Alertas.** Se generan al crearse un reporte Grave/Muy grave (o al escalarse a esa gravedad) y cada vez que un reporte
deja al estudiante con 3 o más contables en el ciclo. Quedan en la bandeja de Subdirección (que Dirección también ve) y,
además, se envían por correo a los usuarios activos con rol Subdirección. El correo **no incluye la descripción de los
hechos**, solo folio, estudiante, grupo, incidencia y gravedad, más el enlace. Si no hay SMTP configurado o el envío falla,
la alerta se conserva en la bandeja y se registra el motivo. Variables: `SMTP_HOST`, `SMTP_PORT` (465 usa SSL), `SMTP_USER`,
`SMTP_PASSWORD`, `SMTP_FROM`, `SMTP_STARTTLS` y `APP_URL` (para los enlaces del correo).

### Fase 6: exportaciones, bitácora y seguridad

| Método | Ruta | Quién |
|---|---|---|
| GET | `/exportaciones/estudiantes/{id}` | Excel de los reportes de un estudiante |
| GET | `/exportaciones/grupos/{id}` | Excel de los reportes de un grupo |
| GET | `/exportaciones/carreras/{id}` | Excel de los reportes de una carrera |
| GET | `/bitacora` (`accion`, `usuario_id`, `estudiante_id`, `desde`, `hasta`, `limite`, `offset`) | Solo Administrador |

Parámetros de las exportaciones: `desde`, `hasta` (AAAA-MM-DD) e `incluir_contacto=true`.

**Qué trae el Excel.** Hoja *Resumen* (alcance, quién y cuándo lo generó, totales por gravedad, por estado, sanciones y
reportes sin llamada efectiva) y hoja *Reportes* (una fila por reporte: folio, fecha, estudiante, grupo, carrera,
incidencia, descripción, gravedad, estado, cancelación, si cuenta para la acumulación, autor, llamada y sanción). Incluye los
reportes cancelados, marcados como tales. Máximo 5000 reportes por archivo (acota con fechas). Los textos que Excel
interpretaría como fórmula (`=`, `+`, `-`, `@`) se neutralizan.

**Quién exporta qué.** Cada quien exporta únicamente lo que puede ver en pantalla: Orientación, Subdirección y Dirección,
todo; el tutor, a los estudiantes de sus grupos (todo su historial); el docente, los reportes que él creó. El prefecto y el
Administrador no exportan.

**Contacto opcional.** Con `incluir_contacto=true` se agregan padre/tutor principal, teléfono, correo y domicilio del
estudiante, solo para quienes tienen permiso de ver contacto y, en el caso del tutor, solo de los estudiantes de su grupo
actual (los demás salen en blanco). Pedirlo sin ningún permiso de contacto devuelve 403.

**Bitácora.** Se registra, sin posibilidad de edición, cada exportación (quién, qué alcance, cuántas filas, si llevó
contacto) y cada consulta en pantalla de la ficha de un estudiante o del seguimiento de llamadas (donde aparecen teléfonos y
domicilio). Solo el Administrador la consulta (`/bitacora`, menú *Bitácora*).

**Seguridad.**
- **Bloqueo por intentos:** 5 intentos fallidos seguidos bloquean la cuenta 15 minutos (HTTP 429, `CUENTA_BLOQUEADA`), aun con la
  contraseña correcta. Un acceso correcto reinicia el contador; el Administrador desbloquea restableciendo la contraseña.
- **Cierre de sesiones:** cambiar o restablecer la contraseña y desactivar la cuenta invalidan los tokens anteriores
  (`sesion_version`). Al cambiar la contraseña la API entrega tokens nuevos para la sesión actual.
- **Cabeceras:** `nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`, CSP restrictiva y `Cache-Control: no-store`
  en la API; HSTS en producción. nginx añade las suyas a la aplicación web.
- **Producción:** con `APP_ENV=production` el sistema no arranca si `SECRET_KEY` mide menos de 32 caracteres o parece la clave de ejemplo.

### Dashboard de inicio

`GET /dashboard?rango=periodo|mes|30dias` (cualquier usuario autenticado). Devuelve indicadores y series ya recortados a lo
que el usuario puede ver: Orientación, Subdirección y Dirección, todo el plantel; el tutor, sus grupos más lo que creó; el
docente, lo que creó; prefecto y Administrador no reciben datos (`alcance: "ninguno"`). Incluye total del rango y comparación
del mes actual contra el anterior, reportes por gravedad, estado, tipo de incidencia, grupo y carrera, la serie en el tiempo
(por semana en el periodo escolar, por día en mes o 30 días), pendientes de llamada (solo roles directivos), alertas
pendientes (solo quien ve la bandeja) y los estudiantes con 2 o más reportes en su ciclo abierto. Las gráficas son SVG/CSS
propios (sin librerías), con tabla alternativa en cada una.

## Despliegue en producción

Stack completo en `docker-compose.yml` (PostgreSQL 18 + backend + frontend con healthchecks y volúmenes persistentes). Para publicarlo en la nube, consulta **[DESPLIEGUE.md](DESPLIEGUE.md)**.

1. Copia `.env.example` a `.env`, pon `APP_ENV=production`, una `POSTGRES_PASSWORD` fuerte, una `SECRET_KEY` aleatoria
   (`python -c "import secrets; print(secrets.token_urlsafe(48))"`) y `APP_URL` con la dirección real (la de los enlaces del correo).
2. `docker compose up -d --build`. Aplica las migraciones al arrancar y publica solo el puerto `HTTP_PORT` (8080 por defecto).
3. **HTTPS:** el contenedor web habla HTTP. Ponle delante un proxy del plantel que termine TLS (Caddy, nginx o el que use
   tu infraestructura) y apunta a `http://servidor:80`. Los datos son de menores: no los expongas sin https.
4. Crea el primer Administrador: `docker compose exec backend python -m app.cli crear-usuario --nombre "Nombre" --correo correo@dominio --roles ADMINISTRADOR` y registra desde ahí al resto del personal.

## Respaldos

`scripts/respaldo.sh` guarda en `respaldos/` un `pg_dump` (`bd-FECHA.dump`) y las evidencias (`uploads-FECHA.tar.gz`), verifica
que no estén vacíos y conserva los últimos 14 (`CONSERVAR`). En producción: `COMPOSE_FILE=docker-compose.yml scripts/respaldo.sh`.
Prográmalo a diario (cron) y **copia los archivos fuera del servidor**: contienen datos personales; guárdalos con acceso restringido.

`scripts/restaurar.sh respaldos/bd-FECHA.dump [respaldos/uploads-FECHA.tar.gz]` los restaura (pide escribir RESTAURAR). **Prueba una
restauración en un equipo aparte antes de depender de los respaldos.**

## Cómo proteger un endpoint nuevo

```python
@bp.post("/reportes")
@requiere_permiso(Permiso.CREAR_REPORTE)
def crear_reporte(): ...
```

## Regla de dependencias

`interfaces` → `application` → `domain`; `infrastructure` implementa los puertos de `application`.
Solo `container.py` conoce las implementaciones concretas.

Cada caso de uso recibe una **unidad de trabajo** (`UnidadDeTrabajo`) que abre la transacción al entrar
en `with uow:` y descarta todo lo no confirmado con `uow.commit()` al salir. Los repositorios están
separados por agregado en `application/ports/repositorios/`, y la entrada HTTP se valida con esquemas
pydantic en `interfaces/api/schemas/`.
