import sys
import json
import os

from .constants import CONFIG_DIR, SETTINGS_FILE


class Settings:
    DEFAULTS = {
        'theme':         'dark',
        'font_size':     10,
        'max_items':     100,
        'max_pinned':    10,
        'panel_width':   35,   # percent of screen width  (25–60)
        'panel_height':  70,   # percent of screen height (50–100)
        'show_metadata': False,
        'word_wrap':     False,
    }

    _RANGES = {
        'panel_width':  (25, 60),
        'panel_height': (50, 100),
        'font_size':    (8, 24),
        'max_items':    (10, 1000),
        'max_pinned':   (1, 50),
    }

    def __init__(self):
        self._data = dict(self.DEFAULTS)
        self._load()

    def _load(self):
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for k, v in data.items():
                        if k in self.DEFAULTS:
                            default = self.DEFAULTS[k]
                            if isinstance(default, bool):
                                self._data[k] = bool(v)
                            else:
                                coerced = type(default)(v)
                                if k in self._RANGES:
                                    lo, hi = self._RANGES[k]
                                    coerced = max(lo, min(hi, coerced))
                                self._data[k] = coerced
        except Exception:
            pass

    def save(self):
        try:
            os.makedirs(CONFIG_DIR, exist_ok=True)
            with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self._data, f, indent=2)
        except Exception as e:
            print(f'[ClipKeeper] settings save error: {e}', file=sys.stderr)

    @property
    def theme(self):         return self._data['theme']
    @property
    def font_size(self):     return self._data['font_size']
    @property
    def max_items(self):     return self._data['max_items']
    @property
    def max_pinned(self):    return self._data['max_pinned']
    @property
    def panel_width(self):   return self._data['panel_width']
    @property
    def panel_height(self):  return self._data['panel_height']
    @property
    def show_metadata(self): return self._data['show_metadata']
    @property
    def word_wrap(self):     return self._data['word_wrap']

    def apply(self, **kwargs):
        """Update one or more settings and persist."""
        for k, v in kwargs.items():
            if k in self.DEFAULTS:
                default = self.DEFAULTS[k]
                self._data[k] = bool(v) if isinstance(default, bool) else type(default)(v)
        self.save()


settings = Settings()
