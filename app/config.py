import os

class Settings:
    database_url = os.getenv("DATABASE_URL", "sqlite:///./deathradar.db")
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+psycopg://", 1)
    elif database_url.startswith("postgresql://") and "+psycopg" not in database_url:
        database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
    admin_password = os.getenv("ADMIN_PASSWORD", "")
    secret_key = os.getenv("SECRET_KEY", "")
    guild_ally = os.getenv("GUILD_ALLY", "Chora pra Warning")
    guild_enemy = os.getenv("GUILD_ENEMY", "Vanguard")
    deaths_url = os.getenv("DEATHS_URL", "https://telaria.aurera-global.com/?view=ultimas_mortes")
    poll_interval_seconds = max(15, int(os.getenv("POLL_INTERVAL_SECONDS", "30")))

settings = Settings()
