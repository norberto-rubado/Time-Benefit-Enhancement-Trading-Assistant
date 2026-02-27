FROM swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/node:20-alpine AS build

WORKDIR /app

COPY package.json ./
RUN npm config set registry https://registry.npmmirror.com && npm install

COPY . .
RUN npm run build

FROM swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html

# nginx.conf is mounted via docker-compose volume
EXPOSE 80
