FROM cgr.dev/chainguard/node:latest-dev@sha256:3d740b8a4a96b91e86ab9b3c145b1a9b3e032a9a01a1d84ea7695fc8ab51c7ca AS dependencies

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

FROM cgr.dev/chainguard/node:latest@sha256:105c8e7e503ea8f45553b9cc5aa0d24e80499bcc7c860dff54449e7c01d9be79 AS runtime

WORKDIR /app

ENV NODE_ENV=production

COPY --from=production-dependencies --chown=65532:65532 /app/node_modules ./node_modules
COPY --from=build --chown=65532:65532 /app/package.json ./package.json
COPY --from=build --chown=65532:65532 /app/.next ./.next

USER 65532

EXPOSE 3000

CMD ["./node_modules/next/dist/bin/next", "start"]
