# Руководство администратора (Deployment Guide)

Документ для развёртывания **Anonymous Verified Reviews System** на production-сервере и действий при типовых сбоях.

Для локальной разработки см. [README.md](../README.md). Настройка Telegram — в [TELEGRAM.md](TELEGRAM.md).

---

## 1. Требования к серверу

### Минимальная конфигурация (тест / мало пользователей)

| Параметр | Значение |
|----------|----------|
| ОС | Ubuntu 22.04 LTS / Debian 12 (рекомендуется); допустимы другие Linux с Docker |
| CPU | 2 vCPU |
| RAM | 2 GB |
| Диск | 20 GB SSD (свободно ≥ 5 GB под образы, логи и БД) |
| Сеть | Исходящий доступ к `api.telegram.org` (если используется бот) |

### Рекомендуемая конфигурация (production)

| Параметр | Значение |
|----------|----------|
| CPU | 4 vCPU |
| RAM | 4 GB |
| Диск | 40+ GB SSD |
| Резервное копирование | Ежедневный `pg_dump`, хранение вне сервера |

### Программное обеспечение на сервере

- Docker Engine 24+ и Docker Compose v2
- Git
- Nginx или Apache (обратный прокси, TLS)
- `curl` для проверки health-check

Порты, которые слушает приложение **до** прокси (внутри хоста):

| Сервис | Порт | Примечание |
|--------|------|------------|
| API (FastAPI) | `8000` | Публичный доступ — только через прокси |
| Frontend (Vite) | `5173` | В production предпочтительно отдавать статику через Nginx |
| PostgreSQL | `5433` | **Не публиковать** в интернет; только localhost / внутренняя сеть Docker |

---

## 2. Подготовка к развёртыванию

### 2.1. Клонирование и конфигурация

```bash
git clone https://github.com/Kotbuz/Isfcavr-fork-by-kotbuz.git
cd Isfcavr-fork-by-kotbuz
git checkout maintenance

cp .env.example .env
```

Заполните `.env` **production-значениями** (не оставляйте пароли из примера):

```env
DB_HOST=db
DB_PORT=5432
DB_NAME=reviews_db
DB_USER=admin_user
DB_PASSWORD=<сильный_уникальный_пароль>

API_BASE_URL=https://api.example.com
PUBLIC_API_BASE_URL=https://api.example.com

TELEGRAM_BOT_TOKEN=<токен_от_BotFather>
TELEGRAM_BOT_USERNAME=my_reviews_bot
```

> `API_BASE_URL` и `PUBLIC_API_BASE_URL` должны указывать на публичный URL API за reverse proxy.

### 2.2. Персистентное хранилище БД (обязательно для production)

В текущем `docker-compose.yml` том `db_data` объявлен, но **не подключён** к сервису `db`. Перед боевым запуском добавьте в секцию `db`:

```yaml
volumes:
  - db_data:/var/lib/postgresql/data
  - ./db/schema.sql:/docker-entrypoint-initdb.d/01-schema.sql:ro
  - ./db/seed.sql:/docker-entrypoint-initdb.d/02-seed.sql:ro
```

Без `db_data` данные PostgreSQL теряются при пересоздании контейнера.

### 2.3. Запуск стека

```bash
docker compose up --build -d
docker compose ps
curl -f http://127.0.0.1:8000/health
```

Ожидаемый ответ: `{"status":"ok"}`.

Автоматизированный сценарий (тесты + деплой): `deploy.sh`.

---

## 3. Обратный прокси (Nginx)

Nginx принимает HTTPS с интернета и проксирует запросы на контейнеры на `127.0.0.1`.

### 3.1. Пример: API + фронтенд на одном домене

Файл `/etc/nginx/sites-available/reviews.conf`:

```nginx
# Редирект HTTP → HTTPS
server {
    listen 80;
    server_name example.com www.example.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name example.com www.example.com;

    ssl_certificate     /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;

    # Фронтенд (Vite dev / или статика из frontend/dist)
    location / {
        proxy_pass http://127.0.0.1:5173;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # API
    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

При такой схеме в `.env` фронтенда: `VITE_API_BASE_URL=https://example.com/api`.

Активация:

```bash
sudo ln -s /etc/nginx/sites-available/reviews.conf /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

TLS: `sudo certbot --nginx -d example.com -d www.example.com`.

### 3.2. Пример: отдельные поддомены API и фронтенда

```nginx
# api.example.com → FastAPI
server {
    listen 443 ssl http2;
    server_name api.example.com;

    ssl_certificate     /etc/letsencrypt/live/api.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.example.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# app.example.com → фронтенд
server {
    listen 443 ssl http2;
    server_name app.example.com;

    ssl_certificate     /etc/letsencrypt/live/app.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/app.example.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:5173;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

В `.env`: `API_BASE_URL=https://api.example.com`, `VITE_API_BASE_URL=https://api.example.com`.

### 3.3. Production-фронтенд (статическая сборка)

Для стабильной нагрузки предпочтительнее собрать фронтенд и отдавать файлы напрямую:

```bash
cd frontend
npm ci
VITE_API_BASE_URL=https://api.example.com npm run build:web
```

В Nginx замените `proxy_pass` на `root`:

```nginx
location / {
    root /var/www/reviews/frontend/dist;
    try_files $uri $uri/ /index.html;
}
```

---

## 4. Обратный прокси (Apache)

Минимальный VirtualHost для API (`/etc/apache2/sites-available/api.conf`):

```apache
<VirtualHost *:443>
    ServerName api.example.com

    SSLEngine on
    SSLCertificateFile    /etc/letsencrypt/live/api.example.com/fullchain.pem
    SSLCertificateKeyFile /etc/letsencrypt/live/api.example.com/privkey.pem

    ProxyPreserveHost On
    ProxyPass        / http://127.0.0.1:8000/
    ProxyPassReverse / http://127.0.0.1:8000/

    RequestHeader set X-Forwarded-Proto "https"
</VirtualHost>
```

Включение модулей и сайта:

```bash
sudo a2enmod proxy proxy_http ssl headers
sudo a2ensite api.conf
sudo systemctl reload apache2
```

---

## 5. Проверка после развёртывания

| Проверка | Команда / действие |
|----------|-------------------|
| Контейнеры | `docker compose ps` — все сервисы `running` / `healthy` |
| API | `curl -f https://api.example.com/health` |
| Swagger | Открыть `https://api.example.com/docs` (ограничьте доступ в production при необходимости) |
| Фронтенд | Открыть `https://app.example.com` |
| Бот | Отправить `/start` в Telegram; логи: `docker compose logs -f bot` |
| БД | `docker compose exec db pg_isready -U $DB_USER -d $DB_NAME` |

---

## 6. Регламент: восстановление после сбоев

### 6.1. Упала база данных

**Симптомы:** API отвечает `500`, в логах `connection refused` / `could not connect to server`; `docker compose ps` — контейнер `db` в состоянии `Exit` или `unhealthy`.

**Действия администратора:**

1. Зафиксировать время сбоя и сохранить логи:
   ```bash
   docker compose logs --tail=200 db
   docker compose logs --tail=200 api
   ```

2. Проверить статус контейнера:
   ```bash
   docker compose ps db
   ```

3. Перезапустить только БД:
   ```bash
   docker compose restart db
   ```
   Дождаться `healthy` (10–30 с).

4. Если не помогло — поднять стек заново:
   ```bash
   docker compose up -d db
   docker compose up -d api bot frontend
   ```

5. Проверить API:
   ```bash
   curl -f http://127.0.0.1:8000/health
   ```

6. **Если данные повреждены** — восстановление из бэкапа (см. п. 6.3).

7. Задокументировать инцидент (время, причина, действия).

> PostgreSQL не должен быть доступен из интернета. Сбои часто связаны с нехваткой диска или OOM — см. п. 6.2.

### 6.2. Переполнился диск

**Симптомы:** запись в БД падает, Docker не может создать контейнер, в `df -h` раздел `/` или `/var` заполнен на 95%+; в логах `no space left on device`.

**Действия администратора:**

1. Оценить занятость диска:
   ```bash
   df -h
   du -sh /var/lib/docker/* 2>/dev/null | sort -h | tail -10
   docker system df
   ```

2. **Срочно освободить место** (без удаления тома `db_data`):
   ```bash
   docker system prune -f
   journalctl --vacuum-time=7d
   ```
   Удалить старые логи приложений и временные файлы в `/tmp`.

3. Убедиться, что свободно **≥ 2 GB** перед перезапуском сервисов.

4. Перезапустить затронутые контейнеры:
   ```bash
   docker compose up -d
   ```

5. Проверить health API и БД (п. 5).

6. **Профилактика:**
   - настроить ротацию логов Docker / Nginx;
   - мониторинг диска (алерт при > 80%);
   - регулярная очистка неиспользуемых образов: `docker image prune -a` (по регламенту, в окно обслуживания);
   - вынести бэкапы БД на другой сервер / S3.

### 6.3. Резервное копирование и восстановление БД

**Создание бэкапа (ежедневно по cron):**

```bash
docker compose exec -T db pg_dump -U "$DB_USER" "$DB_NAME" | gzip > /backup/reviews_$(date +%F).sql.gz
```

**Восстановление из бэкапа:**

```bash
# Остановить API и бот, чтобы не было записей во время restore
docker compose stop api bot

gunzip -c /backup/reviews_2026-06-01.sql.gz | docker compose exec -T db psql -U "$DB_USER" -d "$DB_NAME"

docker compose start api bot
curl -f http://127.0.0.1:8000/health
```

---

## 7. Обновление версии приложения

```bash
cd /opt/reviews   # каталог проекта
git pull origin maintenance
docker compose up --build -d
curl -f http://127.0.0.1:8000/health
```

При изменении схемы БД примените миграции из `db/` вручную или через `psql` до перезапуска API.

---

## 8. Безопасность (краткий чек-лист)

- [ ] Пароли в `.env` уникальны, файл не в git (`chmod 600 .env`)
- [ ] PostgreSQL не проброшен на `0.0.0.0:5433` в production (убрать `ports` у `db` или bind только `127.0.0.1`)
- [ ] TLS на Nginx/Apache, HSTS при возможности
- [ ] Ограничить доступ к `/docs` по IP или basic auth
- [ ] Регулярные бэкапы и проверка восстановления раз в квартал

---

## 9. Контакты и эскалация

При недоступности сервиса более 15 минут после шагов из раздела 6:

1. Уведомить ответственного за инфраструктуру / Team Lead.
2. Перевести сайт в режим обслуживания (статическая страница в Nginx), если API не восстанавливается.
3. Сохранить логи: `docker compose logs > incident_$(date +%F_%H%M).log`.
