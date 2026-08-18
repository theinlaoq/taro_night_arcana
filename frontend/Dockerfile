FROM nginx:1.27-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY . /usr/share/nginx/html/
RUN cp "/usr/share/nginx/html/Ночной Аркан.dc.html" /usr/share/nginx/html/index.html \
    && rm -f /usr/share/nginx/html/mock-tarot-backend.js

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget -qO- http://127.0.0.1:8080/ >/dev/null || exit 1
