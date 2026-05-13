# Build stage
FROM node:18-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

ARG VITE_API_URL=http://localhost:18080

ENV VITE_API_URL=$VITE_API_URL

RUN npm run build

# Production stage
FROM node:18-alpine

RUN addgroup -S appgroup && adduser -S appuser -G appgroup

WORKDIR /app

RUN npm install -g serve

COPY --from=builder /app/dist ./dist

USER appuser

EXPOSE 3000

CMD ["serve", "-s", "dist", "-l", "3000"]
