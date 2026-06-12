FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY frontend/package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY frontend/ .

# API base URL is baked into the bundle at build time.
# Railway injects service variables during build; this ARG also allows
# `docker build --build-arg VITE_API_BASE_URL=...`.
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

# Build for production
RUN npm run build

# Production stage with Nginx
FROM nginx:alpine

# Railway (and other PaaS) inject the port via $PORT at runtime.
# Default to 80 for local `docker run`. The nginx:alpine image runs
# envsubst on /etc/nginx/templates/*.template at startup, so ${PORT}
# in the template is replaced with this value.
ENV PORT=80

# Copy nginx config template (port is templated via $PORT)
COPY frontend/nginx.conf.template /etc/nginx/templates/default.conf.template

# Copy built assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose port (informational — actual port comes from $PORT)
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s \
    CMD wget --quiet --tries=1 --spider http://localhost:${PORT}/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
