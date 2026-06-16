# ── Build stage ──────────────────────────────────────────────────────────────
# pinned: node:20 (2026-06-16)
FROM node:20@sha256:4232dd95f26d0e887f17756da8df31c4608cd53285f74f95ca0878e432ff6625 AS builder

WORKDIR /app

ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=${VITE_API_URL}
ENV PNPM_HOME=/pnpm
ENV PATH=$PNPM_HOME:$PATH

# Use corepack-managed pnpm for deterministic and cache-friendly installs
RUN corepack enable

# Copy dependency files
COPY pnpm-lock.yaml package.json ./

# Install dependencies using persistent pnpm store cache
RUN --mount=type=cache,id=pnpm-store,target=/pnpm/store \
	pnpm install --prefer-offline --frozen-lockfile

# Copy source code
COPY . .

# Build
RUN pnpm run build

# ── Runtime stage ────────────────────────────────────────────────────────────
# pinned: node:20-alpine (2026-06-16)
FROM node:20-alpine@sha256:6178e78b972f79c335df281f4b7674a2d85071aae2af020ffa39f0a770265435

WORKDIR /app

# Install serve for static file serving
RUN npm install -g serve

# Copy built assets
COPY --from=builder /app/dist ./dist

EXPOSE 3000

CMD ["serve", "-s", "dist", "-l", "3000"]
