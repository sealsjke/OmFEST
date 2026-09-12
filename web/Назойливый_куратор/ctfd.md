# Инструкция: task-образы и docker-compose архивы для CTFd (плагин `instances`)

## Формат архива
- Поддерживаются: `.zip`, `.tar.gz`, `.tgz`, `.tar`
- В **корне** архива должен лежать `docker-compose.yaml` (или `.yml`, `compose.yaml`/`compose.yml`)
- Рядом — все файлы, на которые ссылается `build.context` (обычно Dockerfile + код таска)

## Минимальный архив (один контейнер, tcp)
```
task.tar.gz
├── docker-compose.yaml
└── Dockerfile
```
```yaml
services:
  app:
    build: .
    environment:
      FLAG: ${FLAG}     # флаг от CTFd (сгенерированный или заданный админом)
      PORT: ${PORT}     # внутренний порт таска из формы
    ports:
      - "1337"          # только container-порт; наружу порт выделит плагин (15000-20000)
```
Не указывайте в `ports` хост-порт слева (вида `1337:1337`) — публикуется автоматически.
Достаточно `ports: - "1337"` или `expose: - "1337"`.

## Лимиты
- Диск RW-слоя контейнера (работает после переезда на XFS+pquota):
  ```yaml
  services:
    app:
      storage_opt:
        size: 512m
  ```
- Тома (per-instance, не общие):
  ```yaml
  volumes:
    pgdata:
      x-ctfd-quota: 200m   # нестандартное поле плагина, жёсткий лимит на xfs
  services:
    db:
      image: postgres:17-alpine
      volumes: [ "pgdata:/var/lib/postgresql/data" ]
  ```
  Каждый инстанс получает СВОЙ том `<inst-...>-pgdata` с квотой.
- Память/кол-во процессов задаётся в форме челленджа (mem_limit, pids_limit=256).

## Переменные окружения
`FLAG` и `PORT` передаются каждому сервису. В `environment` можно использовать интерполяцию:
- `${FLAG}` / `$FLAG` — подставится значение
- свои значения из compose сохраняются и перекрываются только системными (FLAG/PORT)

## Флаги
- **Статический**: задан в челлендже → передаётся как `FLAG`.
- **Динамический (CTFd-generated)**: поле флага пустое → при первом старте CTFd генерирует
  `ctf{16hex}`, сохраняет его в челлендже (сабмиты проверяются) и передаёт через `FLAG`.

## Что запрещено
- `network_mode: host`, host binds (`/etc`, `/root`, любые абсолютные пути в volumes) — игнорируются
- `privileged: true` — игнорируется
- порты наружу кроме primary-сервиса; primary = значение поля "Primary Service" или первый сервис

## Требования к Dockerfile
- Сервис **обязан слушать порт** (иначе соединение примется docker-прокси и закроется):
  socat/nc/python http.server — любой listener
- Порт слушайте тот, что указан в `ports`/`expose`; читайте `$PORT`/`$FLAG` из env
- Сервисы с `sleep`/daemon: не используйте `restart: always`-логику в CMD; рестарт-политику
  ставит плагин (unless-stopped)

## Web-таски
- Публикуются по `http://<hash>.ctfd.hexagrammic.ru` (domain настраивается в админке)
- Плагин ставит traefik-лейблы сам; в compose ничего для роутинга не нужно
- Внутренний HTTP-порт = Container Port в форме (или первый порт из compose primary-сервиса)

## Проверка
1. Соберите архив, создайте челлендж (тип `instance`), приложите архив
2. Админка → Instances — в таблице «Compose tasks» видны сервисы/порты/лимиты
3. Запустите инстанс на странице челленджа, подключитесь по выданному адресу
