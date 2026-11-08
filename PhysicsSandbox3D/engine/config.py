import json
import os
import sys
from pathlib import Path

ROOT = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parents[1]))
DATA = Path(os.environ.get('PHYSICS_SANDBOX_DATA', Path.home() / 'PhysicsSandbox'))
DEFAULTS = {'resolution': [1280, 720], 'fov': 80, 'quality': 'medium', 'fog': True}


def load_settings():
    try:
        value = json.loads((DATA / 'settings.json').read_text())
        result = DEFAULTS | {k: v for k, v in value.items() if k in DEFAULTS}
        if result['resolution'] not in ([1280,720], [1600,900], [1920,1080]):
            result['resolution'] = DEFAULTS['resolution']
        if result['quality'] not in ('low','medium','high'): result['quality'] = 'medium'
        result['fov'] = max(60, min(110, float(result['fov'])))
        return result
    except (OSError, ValueError, TypeError, AttributeError):
        return dict(DEFAULTS)


def save_settings(settings):
    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / 'settings.json').write_text(json.dumps(settings, indent=2))
