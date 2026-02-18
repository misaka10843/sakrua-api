from app.core.config import settings

TORTOISE_ORM = {
    "connections": {
        "default": settings.DB_URL,
    },
    "apps": {
        "models": {
            "models": settings.DB_MODELS,
            "default_connection": "default",
        },
    },
}