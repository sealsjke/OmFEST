FROM node:22-alpine AS build
WORKDIR /app
COPY package*.json ./
ARG NPM_REGISTRY=https://registry.npmmirror.com
RUN --mount=type=cache,target=/root/.npm npm config set registry "$NPM_REGISTRY" \
 && npm config set fetch-retries 5 \
 && npm config set fetch-retry-mintimeout 2000 \
 && npm config set fetch-retry-maxtimeout 20000 \
 && npm ci --no-audit --no-fund --prefer-offline
COPY tsconfig.json ./
COPY src ./src
RUN npm run build

FROM build AS production-deps
RUN npm prune --omit=dev --no-audit --no-fund

FROM node:22-alpine AS production
ENV NODE_ENV=production
WORKDIR /app
COPY --from=production-deps --chown=node:node /app/package.json ./package.json
COPY --from=production-deps --chown=node:node /app/node_modules ./node_modules
COPY --from=build --chown=node:node /app/dist/src ./dist
USER node
EXPOSE 3000
CMD ["node", "dist/server.js"]
