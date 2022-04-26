import gettext
from pathlib import Path

from core import config


def get_translator(lang: str = config.LANGUAGE):
    trans = gettext.translation(
        'movies',
        localedir=Path(config.BASE_DIR, config.LOCALE_PATH),
        languages=(lang,)
    )
    return trans.gettext


gettext_lazy = get_translator()
