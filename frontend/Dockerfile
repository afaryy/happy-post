FROM cgr.dev/chainguard/node:latest-dev@sha256:d543de1e29036a65ab270e2069672aa29fae3999e089bc491a9f9094ad2d6ac2 AS dependencies

USER root

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

FROM dependencies AS build

COPY . ./

ARG BACKEND_BASE_URL
ENV BACKEND_BASE_URL=${BACKEND_BASE_URL}

RUN npm run build

FROM dependencies AS production-dependencies

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci --omit=dev

FROM cgr.dev/chainguard/node:latest@sha256:7740ce8ef7cce4b0892e85813cbb39abe48c56bd48290cb18b9ea721480263f3 AS runtime

WORKDIR /app

ENV NODE_ENV=production

COPY --from=production-dependencies --chown=65532:65532 /app/node_modules ./node_modules
COPY --from=build --chown=65532:65532 /app/package.json ./package.json
COPY --from=build --chown=65532:65532 /app/.next ./.next

EXPOSE 3000

CMD ["./node_modules/next/dist/bin/next", "start"]
