FROM node:22-alpine AS deps

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci

FROM node:22-alpine AS builder

WORKDIR /app/frontend
ENV NEXT_TELEMETRY_DISABLED=1
COPY --from=deps /app/frontend/node_modules ./node_modules
COPY frontend ./
RUN npm run build

FROM node:22-alpine AS runner

WORKDIR /app/frontend
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV NEXT_DIST_DIR=.next
COPY --from=builder /app/frontend ./
EXPOSE 3000
CMD ["npm", "run", "start", "--", "--port", "3000"]
