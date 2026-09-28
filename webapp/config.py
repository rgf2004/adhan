"""Shared paths/constants for the admin web app."""

import sys
from os.path import dirname, abspath, join as pathjoin

ROOT_DIR = dirname(dirname(abspath(__file__)))
sys.path.insert(0, ROOT_DIR)
sys.path.insert(0, pathjoin(ROOT_DIR, 'crontab'))

SETTINGS_PATH = pathjoin(ROOT_DIR, 'settings.json')
SETTINGS_EXAMPLE_PATH = pathjoin(ROOT_DIR, 'settings.example.json')
BACKUP_PATH = SETTINGS_PATH + '.bak'
UPDATE_SCRIPT = pathjoin(ROOT_DIR, 'updateAzaanTimers.py')
UPLOAD_DIR = pathjoin(ROOT_DIR, 'uploads')
MAWAQIT_DIR = pathjoin(ROOT_DIR, 'mawaqit_files')
CRON_COMMENT = 'rpiAdhanClockJob'
PRAYER_KEYS = ['fajr', 'dhuhr', 'asr', 'maghrib', 'isha']
METHODS = ['MWL', 'ISNA', 'Egypt', 'Makkah', 'Karachi', 'Tehran', 'Jafari']
