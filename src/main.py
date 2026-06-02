from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse

from src.db.database import init_db
from src.routers import box_router, feedback_router
from src.routers.auth_router import router as auth_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)
app.include_router(box_router.router)
app.include_router(feedback_router.router)
app.include_router(auth_router)

# Create tables at import time so TestClient/pytest works reliably.
init_db()


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes,
    )
    openapi_schema.setdefault("components", {}).setdefault("securitySchemes", {})["BearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "token",
    }
    for path in openapi_schema.get("paths", {}).values():
        for operation in path.values():
            if isinstance(operation, dict):
                operation.setdefault("security", []).append({"BearerAuth": []})
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


@app.get("/", response_class=HTMLResponse)
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


@app.get("/health")
def health():
    return {"status": "ok"}
