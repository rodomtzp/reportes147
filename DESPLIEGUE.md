# Gran Entregable Final – Guía de despliegue

## 1. Contenerización (ya está en el repositorio)

| Requisito | Archivo |
|---|---|
| Backend multi-etapa (wheels → imagen final, usuario sin privilegios, healthcheck). Equivale a `pnpm` + `prisma migrate deploy`: aquí es `pip` + `alembic upgrade head` | `backend/Dockerfile` |
| Frontend multi-etapa (pnpm → Nginx) con soporte de React Router (`try_files $uri /index.html`) | `frontend/Dockerfile`, `frontend/nginx.conf` |
| PostgreSQL 18 + backend + frontend, healthchecks y volúmenes persistentes (`pgdata`, `uploads`) | `docker-compose.yml` |
| Desarrollo con recarga en caliente | `docker-compose.dev.yml` |

Prueba local (si venías de la versión anterior con PostgreSQL 16, borra su volumen: `docker compose -f docker-compose.dev.yml down -v`):

```bash
cp .env.example .env     # APP_ENV=production, SECRET_KEY nueva, POSTGRES_PASSWORD fuerte
docker compose up -d --build
docker compose ps        # los 3 servicios deben quedar "healthy"
curl http://localhost:8080/api/v1/health      # {"estado":"ok"}
docker compose exec backend python -m app.cli crear-usuario --nombre "Admin" --correo admin@cbtis147.edu.mx --roles ADMINISTRADOR
```

Recomendado para el repositorio: genera `frontend/pnpm-lock.yaml` con `cd frontend && corepack enable && pnpm install` y súbelo.

## 2. Repositorio en GitHub

```bash
git init && git add . && git commit -m "Sistema de reportes CBTis 147"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/cbtis147-reportes.git
git push -u origin main
```
Verifica que `.env` NO se suba (está en `.gitignore`); solo `.env.example`. Hazlo público o agrega al instructor como colaborador.

## 3. Nube (ejemplo con Render; Railway o Fly.io siguen el mismo esquema)

Se crean tres recursos, en este orden. Usa la misma región para los tres.

1. **Base de datos PostgreSQL** (elige la versión 18 si el proveedor la ofrece). Copia la *Internal Database URL*.
   Las migraciones se aplican solas cuando arranca el backend (`alembic upgrade head`).
2. **Backend** – *Web Service*, Runtime Docker, Root Directory `backend`. Variables:
   - `DATABASE_URL` = URL interna de la BD (acepta `postgres://…`; la app la convierte)
   - `APP_ENV=production`
   - `SECRET_KEY` = `python -c "import secrets; print(secrets.token_urlsafe(48))"`
   - `APP_URL` = URL pública del frontend (paso 3)
   - Health Check Path: `/api/v1/health`
   - Render inyecta `PORT`; el Dockerfile ya lo usa.
   - Evidencias: sin disco persistente se pierden en cada despliegue. Agrega un *Disk* montado en `/data/uploads` (plan de pago) o acepta esa limitación en la demo.
3. **Frontend** – *Web Service*, Runtime Docker, Root Directory `frontend`. Variable única:
   - `BACKEND_URL` = URL pública del backend, p. ej. `https://reportes-api.onrender.com`

   Nginx reenvía `/api/` al backend, así que el navegador solo habla con el dominio del frontend (mismo origen: no necesita CORS).
4. Crea el primer administrador desde la *Shell* del servicio backend:
   `python -m app.cli crear-usuario --nombre "Admin" --correo admin@cbtis147.edu.mx --roles ADMINISTRADOR`

Los planes gratuitos duermen el servicio tras inactividad (la primera petición tarda ~1 min) y algunas bases gratuitas caducan: abre la app antes de la entrega.

## 4. Enlaces a subir a la plataforma

1. Repositorio: `https://github.com/TU_USUARIO/cbtis147-reportes`
2. Frontend: `https://TU-FRONTEND.onrender.com`
3. Backend (health check): `https://TU-BACKEND.onrender.com/api/v1/health` → `{"estado":"ok"}`

## 5. Lista de verificación

- [ ] `docker compose ps` muestra db, backend y frontend en *healthy*
- [ ] Recargar una ruta interna (p. ej. `/reportes`) en el frontend no da 404
- [ ] Login con el administrador desde la URL pública
- [ ] El health check del backend responde desde internet
- [ ] No hay contraseñas ni `.env` en el repositorio

## 6. Atajo para Render: `render.yaml` (Blueprint)

El repositorio incluye `render.yaml`. En Render: **New + → Blueprint →** elige tu repositorio. Crea la base (PostgreSQL 18), el backend y el frontend; te pide `APP_URL` y `BACKEND_URL`.
Como las URLs públicas solo existen tras crear los servicios: escribe valores provisionales, y cuando Render asigne los dominios (`https://reportes-api-xxxx.onrender.com` y `https://reportes-web-xxxx.onrender.com`) corrígelos en *Environment* de cada servicio y guarda (redespliega solo).
