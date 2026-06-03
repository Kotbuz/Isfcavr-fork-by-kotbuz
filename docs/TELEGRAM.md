# Telegram: привязка и уведомления

## Почему не работает из Docker

Контейнеры ходят в `https://api.telegram.org`. Если провайдер блокирует Telegram, из Docker часто получают:

```text
ConnectionRefusedError ... api.telegram.org:443
```

**tg-ws-proxy** ([Flowseal/tg-ws-proxy](https://github.com/Flowseal/tg-ws-proxy)) — MTProto для **Telegram Desktop**, не HTTP/SOCKS для Bot API. Ссылка `https://t.me/proxy?...` настраивает только клиент, не переменную `TELEGRAM_PROXY_URL`.

---

## VPN VLESS / XHTTP (OdaVPN и аналоги)

**Строку VLESS/XHTTP в `.env` вставлять не нужно** — это настройка только VPN-клиента на ПК.

| Куда | Что |
|------|-----|
| VPN-клиент (Hiddify, v2rayN, Nekoray…) | Подписка Oda: протокол **VLESS**, транспорт **XHTTP** — как в панели |
| Корневой **`.env`** | `TELEGRAM_BOT_TOKEN`, `INTERNAL_BOT_SECRET`, `TELEGRAM_BOT_USERNAME`, БД, `VITE_*`, `PUBLIC_FRONTEND_URL` |
| **`TELEGRAM_PROXY_URL`** | Только если в клиенте включён **локальный SOCKS5/HTTP** (см. ниже) |

### Минимум в `.env` (корень проекта)

```env
DB_HOST=localhost
DB_PORT=5433
DB_NAME=...
DB_USER=...
DB_PASSWORD=...

TELEGRAM_BOT_TOKEN=...          # от @BotFather
TELEGRAM_BOT_USERNAME=KotbuzBot
INTERNAL_BOT_SECRET=...         # любая длинная строка, одна на api и бот

VITE_API_BASE_URL=http://localhost:8000
PUBLIC_FRONTEND_URL=http://localhost:5173

TELEGRAM_PROXY_URL=             # пусто, пока не нашли локальный SOCKS
```

### Шаг 1 — привязка Telegram (VLESS уже работает на ПК)

1. Включите OdaVPN (VLESS).
2. `docker compose up --build`
3. Второй терминал: `.\scripts\run-bot-local.ps1`
4. Сайт → админка → «Привязать Telegram» → ссылка → Start в боте → обновить страницу.

В файлы **ничего про VLESS** не пишется — бот на Windows идёт через VPN системы.

### Шаг 2 — уведомления (API в Docker)

Контейнер `api` сам не использует VLESS. Нужен **локальный прокси** от VPN-клиента:

1. В приложении Oda/Hiddify/v2rayN откройте настройки → **локальный порт / SOCKS / Mixed / HTTP inbound**.
2. Включите **«доступ из локальной сети» / Allow LAN**.
3. Запомните порт, например `10808`.
4. В `.env`:

```env
TELEGRAM_PROXY_URL=socks5://host.docker.internal:10808
```

5. `docker compose up --build` (перезапуск).

Проверка:

```powershell
docker compose exec api python -c "import httpx; r=httpx.get('https://api.telegram.org', proxy='socks5://host.docker.internal:10808', timeout=15); print(r.status_code)"
```

Если локального SOCKS в клиенте нет — уведомления из Docker не пойдут; привязка через `run-bot-local.ps1` всё равно может работать.

---

## Способ 1 (рекомендуется): бот на ПК, остальное в Docker

1. Запуск без бота в контейнере:

```powershell
cd P:\Practice\Isfcavr-fork-by-kotbuz
docker compose up --build
```

2. В **другом** терминале — бот на Windows (сеть и VPN как у браузера):

```powershell
.\scripts\run-bot-local.ps1
```

3. Привязка: админка → «Привязать Telegram» → открыть ссылку → **Start** в боте.

4. Уведомления при новом отзыве шлёт **API в Docker** — ему тоже нужен доступ к Telegram (способ 2 или 3).

---

## Способ 2: SOCKS5/HTTP-прокси для Docker

Нужен прокси, который слушает на **ПК** (Clash, v2rayN, VPN с «локальный SOCKS»), не MTProto из tg-ws-proxy.

В `.env`:

```env
TELEGRAM_PROXY_URL=socks5://host.docker.internal:1080
```

Порт замените на свой (7890, 10808 и т.д.). В клиенте VPN включите **«Разрешить из локальной сети» / Allow LAN**.

Перезапуск:

```powershell
docker compose --profile docker-bot up --build
```

Проверка из контейнера API:

```powershell
docker compose exec api python -c "import httpx; r=httpx.get('https://api.telegram.org', proxy='socks5://host.docker.internal:1080', timeout=15); print(r.status_code)"
```

(подставьте свой proxy URL)

---

## Способ 3: прокси в Docker Desktop

**Settings → Resources → Proxies → Manual**  
Укажите HTTP-прокси вашего VPN (часто `http://127.0.0.1:7890`).

Перезапустите Docker Desktop, затем `docker compose up`.

---

## Способ 4: бот в Docker с профилем

Если прокси из способа 2 настроен:

```powershell
docker compose --profile docker-bot up --build
```

Без рабочего прокси контейнер `bot` будет падать или переподключаться.

---

## Способ 5: деплой API на VPS за рубежом

На сервере без блокировки Telegram:

- API + bot в Docker **или** только API, бот на VPS;
- в `.env` на сервере без `TELEGRAM_PROXY_URL`;
- `PUBLIC_FRONTEND_URL` — URL вашего фронта.

Локально остаётся только разработка UI.

---

## Способ 6: только привязка без уведомлений

Можно пользоваться сайтом без Telegram: отзывы в админке работают.  
Привязка и push требуют хотя бы одного из способов выше.

---

## Чеклист

| Шаг | Команда / действие |
|-----|-------------------|
| API жив | http://localhost:8000/health |
| Бот жив (локально) | `.\scripts\run-bot-local.ps1` → в логе нет ошибок api.telegram.org |
| Секреты | `INTERNAL_BOT_SECRET` одинаковый в `.env` |
| После привязки | Обновить страницу админки → «Telegram подключён» |
| Уведомление | Отзыв на UUID-ссылку владельца → сообщение в Telegram |

---

## Частые ошибки

- `t.me/proxy?...` в `TELEGRAM_PROXY_URL` — **неверно**
- `127.0.0.1` в Docker — это контейнер, нужен `host.docker.internal`
- tg-ws-proxy порт **1443** — MTProto, не подходит для `TELEGRAM_PROXY_URL`
- Бот в Docker без прокси при блокировке — используйте **способ 1**
