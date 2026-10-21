# ---------- Etapa 1: compilar la SPA con pnpm ----------
FROM node:22-alpine AS build
RUN corepack enable && corepack prepare pnpm@9 --activate
WORKDIR /app
COPY package.json pnpm-lock.yaml* ./
# Con pnpm-lock.yaml en el repo la instalación es reproducible (en CI usa --frozen-lockfile).
RUN pnpm install
COPY . .
RUN pnpm run build

# ---------- Etapa 2: nginx sirve los estáticos y reenvía /api al backend ----------
FROM nginx:1.27-alpine
# BACKEND_URL se sustituye al arrancar (plantilla de la imagen oficial de nginx)
ENV BACKEND_URL=http://backend:5000
COPY nginx.conf /etc/nginx/templates/default.conf.template
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
HEALTHCHECK --interval=15s --timeout=3s --start-period=5s --retries=5 \
  CMD wget -qO- http://127.0.0.1/ >/dev/null || exit 1
