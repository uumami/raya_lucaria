# Glintstone Example -- Build image for testing the framework locally
# Build context: .. (glintstone repo root)
# Maps repo's src/ into the glintstone/src/ structure expected by build scripts

FROM node:20-alpine AS base
RUN apk add --no-cache python3 py3-yaml git

# --- Dependencies ---
FROM base AS deps
WORKDIR /app
COPY src/eleventy/package.json src/eleventy/package-lock.json* ./glintstone/src/eleventy/
RUN cd glintstone/src/eleventy && npm ci --ignore-scripts 2>/dev/null || npm install

# --- Runtime ---
FROM base AS runtime
WORKDIR /app

# Copy installed node_modules from deps stage
COPY --from=deps /app/glintstone/src/eleventy/node_modules ./glintstone/src/eleventy/node_modules

# Copy framework source into glintstone/ structure (as if it were a submodule)
COPY src/ ./glintstone/src/
COPY docs/ ./glintstone/docs/
COPY docker/scripts/ ./glintstone/docker/scripts/
RUN chmod +x glintstone/docker/scripts/*.sh

RUN mkdir -p _site

CMD ["sh", "glintstone/docker/scripts/build.sh"]
