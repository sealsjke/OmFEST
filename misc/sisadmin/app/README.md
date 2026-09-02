## Быстрый запуск

Требуются Docker Engine и Docker Compose v2.

1. Создайте `.env` из примера и задайте секретный флаг:

   cp .env.example .env
   # Отредактируйте FLAG в .env
   
2. Соберите и запустите лабораторию:

   docker compose up --build
   
3. Откройте http://localhost:1337.

Внешний порт можно переопределить: `WEB_PORT=18080 docker compose up --build`.

Локальный `.env` исключён через `.gitignore`. Остановить стенд можно командой `docker compose down`.

## Конфигурация challenge

Таблица адресации и независимые условия validator находятся в [backend/src/config/challenge.ts](backend/src/config/challenge.ts). После изменения пересоберите backend и frontend: frontend получает предназначенную игроку таблицу через `GET /api/challenge`, но не получает внутренний результат validation.

Переменная окружения:

| Имя | Назначение | Обязательность |
| `FLAG` | Секрет, добавляемый только к успешному PC1 → PC2 ping | обязательна в Compose |
| `SESSION_TTL_MS` | Время жизни неактивной сессии, по умолчанию 2 часа | необязательна |
| `API_RATE_LIMIT_PER_MINUTE` | Запросов API в минуту на клиентский IP, по умолчанию 1500 | необязательна |
| `SESSION_CREATE_RATE_LIMIT_PER_MINUTE` | Новых сессий в минуту на IP, по умолчанию 120 | необязательна |
| `MAX_SESSIONS` | Общий предел активных сессий, по умолчанию 300 | необязательна |
| `MAX_SESSIONS_PER_CLIENT` | Предел активных сессий на IP, по умолчанию 120 | необязательна |
| `LOG_LEVEL` | Уровень Fastify logger | необязательна |
| `HOST`, `PORT` | Адрес и порт backend | необязательны |

Настоящий флаг храните только в `.env` или в secret manager оркестратора. `.env.example` содержит лишь placeholder. Production image и frontend bundle флага не содержат. Если backend запущен вне Compose без `FLAG`, он возвращает явный development placeholder вместо challenge-флага.

## Архитектура

- `frontend/` — React, TypeScript, Vite, React Flow и xterm.js. UI отправляет только пользовательские действия и всегда принимает актуальное состояние backend.
- `backend/src/network/` — IPv4 arithmetic, физический граф, link state, L2 traversal, directly connected routing, двунаправленный ping и строгий validator.
- `backend/src/cli/` — собственные state-machine parsers для PC, router и switch. Команды не передаются ОС.
- `backend/src/sessions/` — изолированные in-memory sessions с UUID, TTL cleanup и ограничениями количества сессий.
- `nginx/` — same-origin reverse proxy и статическая раздача production frontend.

Backend хранит устройства, интерфейсы, IP/mask/gateway, admin state и кабели. Link имеет состояние UP, только когда существует и оба интерфейса административно включены. PC и switch порты включены по умолчанию; router-порты требуют `no shutdown`.

Для remote subnet PC проверяет достижимость gateway по L2, router выбирает directly connected network, затем симулятор проверяет L2-доставку к получателю и полный обратный путь. Challenge validator дополнительно требует ровно цепочку `PC1 — SW1 — R1 — SW2 — PC2`, ожидаемую адресацию, отсутствие лишних объектов и UP-состояние всех нужных интерфейсов.

## Поддерживаемые команды

PC Command Prompt:

- `ipconfig`, `ipconfig /all`
- `ping <ip>`
- `help`, `clear`, `exit`

Router CLI:

- `enable`
- `configure terminal`, `conf t`
- `interface gigabitEthernet0/0`, `interface g0/0` и интерфейс `0/1`
- `ip address <ip> <mask>`, `no ip address`
- `shutdown`, `no shutdown`, `exit`, `end`
- `show ip interface brief`, `show running-config`
- `ping <ip>`, `help`, `clear`

Switch CLI:

- `enable`, `configure terminal`, `conf t`
- `interface fastEthernet0/1` / `interface fa0/1` (порты 1–4)
- `shutdown`, `no shutdown`, `exit`, `end`
- `show interfaces status`, `show running-config`, `help`, `clear`

## Admin walkthrough

1. Перетащите устройства в порядке PC, PC, Switch, Switch, Router. Они автоматически получат роли PC1, PC2, SW1, SW2 и R1.
2. Соедините:
   - PC1 `FastEthernet0` ↔ SW1 `FastEthernet0/1`
   - SW1 `FastEthernet0/2` ↔ R1 `GigabitEthernet0/0`
   - R1 `GigabitEthernet0/1` ↔ SW2 `FastEthernet0/1`
   - SW2 `FastEthernet0/2` ↔ PC2 `FastEthernet0`
3. В Desktop → IP Configuration задайте PC1: `192.168.10.10`, `255.255.255.0`, gateway `192.168.10.1`.
4. Настройте R1:

   enable
   configure terminal
   interface g0/0
   ip address 192.168.10.1 255.255.255.0
   no shutdown
   exit
   interface g0/1
   ip address 192.168.20.1 255.255.255.0
   no shutdown
   end
   show ip interface brief
   
5. Задайте PC2: `192.168.20.10`, `255.255.255.0`, gateway `192.168.20.1`.
6. На PC1 выполните `ping 192.168.20.10`. Только этот запрос после полной server-side validation добавит значение `FLAG` к успешному результату.

## Security assumptions

- Frontend и browser state считаются недоверенными; лимиты устройств, интерфейсы, occupancy и конфигурация проверяются backend.
- Нет `/flag` endpoint, `eval`, `exec`, `spawn`, shell parsing, filesystem API или пользовательских путей.
- JSON body ограничен 16 KiB, команды — 200 символами; включены Helmet и rate limiting.
- Nginx задаёт CSP и проксирует API по одному origin.
- Контейнеры работают non-root, без Linux capabilities, с `no-new-privileges` и read-only filesystem.
