# 构建上下文为仓库根目录，先执行 cd frontend && pnpm build
FROM nginx:1.27-alpine

COPY deploy/docker/nginx.conf /etc/nginx/conf.d/default.conf
COPY frontend/apps/admin/dist /usr/share/nginx/html
EXPOSE 80
