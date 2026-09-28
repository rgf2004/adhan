"""Read/write/apply settings.json.

updateAzaanTimers.py never writes settings.json (it's read-only there), so this module is the
sole writer in the whole system. Semantic validation (HH:MM format, allowed methods, mode-specific
required fields) is deliberately NOT duplicated here -- it's deferred to updateAzaanTimers.py itself
via subprocess, so there is exactly one place that validation logic lives.
"""

import copy
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
from collections import namedtuple

from webapp.config import ROOT_DIR, SETTINGS_PATH, SETTINGS_EXAMPLE_PATH, BACKUP_PATH, UPDATE_SCRIPT, PRAYER_KEYS

_lock = threading.Lock()

ApplyResult = namedtuple('ApplyResult', ['returncode', 'stdout', 'stderr'])


def load_settings():
    """Load settings.json, falling back to settings.example.json as a first-run template."""
    path = SETTINGS_PATH if os.path.exists(SETTINGS_PATH) else SETTINGS_EXAMPLE_PATH
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_settings_atomic(data, path=SETTINGS_PATH):
    if os.path.exists(path):
        shutil.copy2(path, BACKUP_PATH)

    fd, tmp_path = tempfile.mkstemp(dir=ROOT_DIR, prefix='.settings.', suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
            f.write('\n')
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
    except BaseException:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


def apply_settings(path=SETTINGS_PATH):
    try:
        proc = subprocess.run(
            [sys.executable, UPDATE_SCRIPT, '--config', str(path)],
            cwd=ROOT_DIR, capture_output=True, text=True, timeout=30,
        )
        return ApplyResult(proc.returncode, proc.stdout, proc.stderr)
    except subprocess.TimeoutExpired as e:
        return ApplyResult(-1, e.stdout or '', 'updateAzaanTimers.py timed out after 30s')


def _coerce_int(value, field_name, errors):
    try:
        return int(value)
    except (TypeError, ValueError):
        errors.append(f'Invalid {field_name}: {value!r} is not a number')
        return None


def _coerce_float(value, field_name, errors):
    try:
        return float(value)
    except (TypeError, ValueError):
        errors.append(f'Invalid {field_name}: {value!r} is not a number')
        return None


def form_to_settings(form, previous):
    """Map a submitted settings form onto a settings dict, preserving unexposed keys.

    Returns (settings_dict, errors). `errors` is a list of outright-garbage-input messages
    (non-numeric volume/lat/lng) caught before we even write to disk; semantic validation of
    well-typed values (HH:MM format, allowed methods, required fields per mode) is left to
    updateAzaanTimers.py via apply_settings().
    """
    errors = []
    data = copy.deepcopy(previous)
    general = data.setdefault('general', {})
    prayers = data.setdefault('prayers', {})

    mode = form.get('mode', general.get('mode', 'calculated'))
    general['mode'] = mode

    lat_raw = form.get('lat', '')
    lng_raw = form.get('lng', '')
    if lat_raw != '' or lng_raw != '':
        lat = _coerce_float(lat_raw, 'general.location.lat', errors)
        lng = _coerce_float(lng_raw, 'general.location.lng', errors)
        general['location'] = {'lat': lat, 'lng': lng}

    method = form.get('method', '').strip()
    if method:
        general['method'] = method

    mawaqit_file = form.get('mawaqit_file', '').strip()
    general['mawaqit_file'] = mawaqit_file or None

    update_time = form.get('update_time', '').strip()
    if update_time:
        general['update_time'] = update_time

    log_file = form.get('log_file', '').strip()
    if log_file:
        general['log_file'] = log_file

    default_audio = form.get('default_audio', '').strip()
    if default_audio:
        general['default_audio'] = default_audio

    default_volume_raw = form.get('default_volume', '')
    if default_volume_raw != '':
        v = _coerce_int(default_volume_raw, 'general.default_volume', errors)
        if v is not None:
            general['default_volume'] = v

    for key in PRAYER_KEYS:
        prayer_cfg = prayers.setdefault(key, {})
        audio = form.get(f'prayers.{key}.audio', '').strip()
        if audio:
            prayer_cfg['audio'] = audio
        volume_raw = form.get(f'prayers.{key}.volume', '')
        if volume_raw != '':
            v = _coerce_int(volume_raw, f'prayers.{key}.volume', errors)
            if v is not None:
                prayer_cfg['volume'] = v
        prayer_cfg['enabled'] = form.get(f'prayers.{key}.enabled') == 'on'

    return data, errors
