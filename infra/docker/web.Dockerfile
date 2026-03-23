FROM node:22-alpine

WORKDIR /app
COPY package.json pnpm-workspace.yaml turbo.json tsconfig.base.json /app/
COPY apps/web /app/apps/web
COPY packages /app/packages
RUN corepack enable && pnpm install
WORKDIR /app/apps/web
CMD ["pnpm", "dev", "--hostname", "0.0.0.0"]
