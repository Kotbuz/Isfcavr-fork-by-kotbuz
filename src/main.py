from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse, JSONResponse

from src.core.logging import get_logger, setup_logging

# Initialize logging as early as possible so imported modules use the
# configured handlers. The following imports must occur after setup;
# ruff/flake8 marks such imports as E402, so we silence that check
# on the specific lines below.
setup_logging()
logger = get_logger(__name__)

from src.db.database import init_db  # noqa: E402
from src.routers import box_router, feedback_router  # noqa: E402
from src.routers.auth_router import router as auth_router  # noqa: E402

app = FastAPI(
    title="Anonymous Verified Reviews API",
    description=(
        "REST API для сбора анонимных отзывов и управления ими владельцем. "
        "Публичные эндпоинты не требуют авторизации; для доступа владельца используйте "
        "`owner_token` (query `token` или заголовок `X-Owner-Token`). "
        "Аккаунт владельца — через `/auth` и Bearer-токен."
    ),
    version="1.0.0",
    openapi_tags=[
        {"name": "boxes", "description": "Создание ящиков отзывов (Box)."},
        {"name": "feedback", "description": "Отправка отзывов и ответы владельца."},
        {"name": "auth", "description": "Регистрация, вход и личный кабинет владельца."},
        {"name": "system", "description": "Служебные эндпоинты (health-check)."},
    ],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    client_host = request.client.host if request.client else "unknown"
    logger.info("HTTP request: %s %s from %s", request.method, request.url.path, client_host)
    try:
        response = await call_next(request)
        logger.info(
            "HTTP response: %s %s -> %s",
            request.method,
            request.url.path,
            response.status_code,
        )
        return response
    except Exception:
        logger.exception("Unhandled exception for request: %s %s", request.method, request.url.path)
        raise


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["Authorization", "Content-Type", "Accept", "X-Owner-Token"],
)
app.include_router(box_router.router)
app.include_router(feedback_router.router)
app.include_router(auth_router)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception for request: %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})


# Create tables at import time so TestClient/pytest works reliably.
init_db()


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    components = openapi_schema.setdefault("components", {})
    security_schemes = components.setdefault("securitySchemes", {})
    security_schemes["BearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "token",
        "description": "Токен из `/auth/register` или `/auth/login`",
    }
    security_schemes["OwnerTokenQuery"] = {
        "type": "apiKey",
        "in": "query",
        "name": "token",
        "description": "Секретный owner_token ящика",
    }
    security_schemes["OwnerTokenHeader"] = {
        "type": "apiKey",
        "in": "header",
        "name": "X-Owner-Token",
        "description": "Секретный owner_token ящика (альтернатива query-параметру)",
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def root():
    return HTMLResponse(
        """
        <html>
            <head>
                <title>Anonymous Feedback API</title>
            </head>
            <body>
                <h1>Anonymous Feedback API</h1>
                <p>Перейдите на страницу документации API, чтобы увидеть доступные команды.</p>
                <ul>
                    <li><a href="/docs">Swagger UI</a> — браузерная документация OpenAPI</li>
                    <li><a href="/redoc">ReDoc</a> — альтернативная документация OpenAPI</li>
                </ul>
                <p>Схема OpenAPI доступна по адресу <code>/openapi.json</code>.</p>
            </body>
        </html>
        """
    )


@app.get(
    "/health",
    tags=["system"],
    summary="Проверка доступности API",
    description="Используется Docker healthcheck и мониторингом.",
    responses={
        200: {
            "description": "Сервис работает",
            "content": {"application/json": {"example": {"status": "ok"}}},
        },
    },
)
def health():
    return {"status": "ok"}
