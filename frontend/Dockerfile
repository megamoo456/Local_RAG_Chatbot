# ==============================================================================
# Frontend Dockerfile — Multi-stage build for Next.js
# ==============================================================================
# Stages:
#   1. base        — Install dependencies
#   2. development — Hot-reload dev server (used in docker-compose)
#   3. builder     — Build production bundle
#   4. production  — Optimized runtime (future deployment)
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage: base — Install dependencies
# ------------------------------------------------------------------------------
FROM node:22-alpine AS base

WORKDIR /app

# Copy package files
COPY package.json package-lock.json ./

# Install dependencies
RUN npm ci

# ------------------------------------------------------------------------------
# Stage: development — Hot-reload server for local development
# ------------------------------------------------------------------------------
FROM base AS development

# Copy entire project
COPY . .

EXPOSE 3000

# Run dev server with hot-reload
CMD ["npm", "run", "dev"]

# ------------------------------------------------------------------------------
# Stage: builder — Build production bundle
# ------------------------------------------------------------------------------
FROM base AS builder

# Copy entire project
COPY . .

# Build the Next.js app
RUN npm run build

# ------------------------------------------------------------------------------
# Stage: production — Optimized runtime image
# ------------------------------------------------------------------------------
FROM node:22-alpine AS production

ENV NODE_ENV=production

WORKDIR /app

# Copy package files
COPY package.json package-lock.json ./

# Install only production dependencies
RUN npm ci --only=production

# Copy built app from builder stage
COPY --from=builder /app/.next /app/.next
COPY --from=builder /app/public /app/public

EXPOSE 3000

# Run production server
CMD ["npm", "start"]
