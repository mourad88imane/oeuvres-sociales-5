# ============================================================
# DOCKERFILE FRONTEND — React + Vite
# ============================================================

# ── Stage 1 : Développement ──────────────────────────────
FROM node:20-alpine AS development

WORKDIR /app

# Copier les fichiers de dépendances
COPY package.json package-lock.json* ./

# Installer les dépendances
RUN npm ci

# Copier le code source
COPY . .

EXPOSE 3000

# Vite dev server avec HMR (Hot Module Replacement)
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"]

# ── Stage 2 : Build de production ────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci --only=production

COPY . .

# Build optimisé
RUN npm run build

# ── Stage 3 : Serveur Nginx de production ────────────────
FROM nginx:alpine AS production

# Copier les fichiers buildés
COPY --from=builder /app/dist /usr/share/nginx/html

# Configuration Nginx pour SPA React (React Router)
COPY nginx-spa.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=10s \
    CMD wget -q --spider http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
