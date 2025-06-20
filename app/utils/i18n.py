from pathlib import Path
from aiogram.utils.i18n import I18n

# Путь к папке locales на два уровня выше (project/locales)
BASE_DIR = Path(__file__).resolve().parents[2]
LOCALES_DIR = BASE_DIR / 'locales'

I18N = I18n(path=str(LOCALES_DIR), default_locale="ru", domain="messages")
_ = I18N.gettext