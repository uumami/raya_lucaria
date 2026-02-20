# Glintstone -- Static site generator for ITAM course materials
# Multi-stage Dockerfile: deps layer (cached) -> runtime layer

# --- Base ---
FROM node:20-alpine AS base
RUN apk add --no-cache python3 py3-yaml git

# --- Dependencies ---
FROM base AS deps
WORKDIR /app
COPY glintstone/src/eleventy/package.json glintstone/src/eleventy/package-lock.json* ./glintstone/src/eleventy/
RUN cd glintstone/src/eleventy && npm ci --ignore-scripts 2>/dev/null || npm install

# --- Runtime ---
FROM base AS runtime
WORKDIR /app

# Copy installed node_modules from deps stage
COPY --from=deps /app/glintstone/src/eleventy/node_modules ./glintstone/src/eleventy/node_modules

# Copy framework source
COPY glintstone/src/ ./glintstone/src/
COPY glintstone/docs/ ./glintstone/docs/
COPY glintstone/docker/scripts/ ./glintstone/docker/scripts/

# Make scripts executable
RUN chmod +x glintstone/docker/scripts/*.sh

# Create output directory
RUN mkdir -p _site

# Default: run the full build
CMD ["sh", "glintstone/docker/scripts/build.sh"]
