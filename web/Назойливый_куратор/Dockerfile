FROM node:20-alpine AS bot-builder
WORKDIR /app/bot
COPY src/bot/package*.json ./
RUN npm install --omit=dev

FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends supervisor ca-certificates && \
    rm -rf /var/lib/apt/lists/*

COPY --from=node:20-bookworm-slim /usr/local/bin/node /usr/local/bin/node

COPY --from=lightpanda/browser:nightly /bin/lightpanda /usr/local/bin/lightpanda

ENV PORT=5000 \
    FLAG="OmFEST{c00k13_st34l1ng_xss_l1k3_4_b0ss}" \
    WELCOME_MESSAGE="Здравствуйте! Я ваш новый начальник отдела. Все служебные отчеты и вопросы направлять в данный чат. Бездельников не потерплю, жду результатов!" \
    SECRET_KEY="corp_promsvyaz_secret_key_1984" \
    BOSS_SECRET="boss_internal_secret_token_12345" \
    WEB_URL="http://web:5000" \
    LIGHTPANDA_URL="ws://lightpanda:9222" \
    CHECK_INTERVAL=15 \
    PYTHONUNBUFFERED=1 \
    NODE_ENV=production

WORKDIR /app/web
COPY src/web/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY src/web/ ./

WORKDIR /app/bot
COPY --from=bot-builder /app/bot/node_modules ./node_modules
COPY src/bot/ ./

COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

WORKDIR /app

EXPOSE 5000

ENTRYPOINT ["/entrypoint.sh"]
