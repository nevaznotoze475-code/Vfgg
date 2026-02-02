# tworker/settings.py
import os
from dataclasses import dataclass
from environs import Env

@dataclass
class BotConfig:
    token: str
    channel_id: int
    super_admin_id: int
    bot_enabled: bool
    drainer_status: bool

@dataclass
class LinksConfig:
    manuals: str
    chat: str
    payouts: str
    connections: str
    info_channel: str
    cryptobot: str
    main_image: str
    drainer_instruction: str

@dataclass
class Settings:
    bot: BotConfig
    links: LinksConfig

def get_settings(path: str):
    env = Env()
    env.read_env(path)
    return Settings(
        bot=BotConfig(
            token=env.str("BOT_TOKEN"),
            channel_id=env.int("CHANNEL_ID"),
            super_admin_id=env.int("SUPER_ADMIN_ID"),
            bot_enabled=env.bool("BOT_ENABLED"),
            drainer_status=env.bool("DRAINER_STATUS")
        ),
        links=LinksConfig(
            manuals=env.str("MANUALS_URL"),
            chat=env.str("CHAT_URL"),
            payouts=env.str("PAYOUTS_URL"),
            connections=env.str("CONNECTIONS_URL"),
            info_channel=env.str("INFO_CHANNEL_URL"),
            cryptobot=env.str("CRYPTOBOT_URL"),
            main_image=env.str("MAIN_IMAGE_URL"),
            drainer_instruction=env.str("DRAINER_INSTRUCTION_URL")
        )
    )

# --- ИЗМЕНЕНИЯ ЗДЕСЬ ---
# Точно так же находим абсолютный путь к .env файлу
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, '.env')

settings = get_settings(ENV_PATH)