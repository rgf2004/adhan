"""List/upload/test-play audio files."""

import os
import subprocess
import threading
from glob import glob
from pathlib import Path

from werkzeug.utils import secure_filename

from webapp.config import ROOT_DIR, UPLOAD_DIR
from webapp.paths import resolve_audio_path, to_repo_relative

_play_lock = threading.Lock()
_current_play = {'proc': None}


def list_audio_files():
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    files = []
    for path in sorted(glob(os.path.join(ROOT_DIR, 'Adhan-*.mp3'))):
        files.append({
            'name': os.path.basename(path),
            'rel_path': to_repo_relative(path),
            'source': 'bundled',
            'size_bytes': os.path.getsize(path),
        })
    for path in sorted(glob(os.path.join(UPLOAD_DIR, '*.mp3'))):
        files.append({
            'name': os.path.basename(path),
            'rel_path': to_repo_relative(path),
            'source': 'uploaded',
            'size_bytes': os.path.getsize(path),
        })
    return files


def save_upload(file_storage):
    """Save an uploaded werkzeug FileStorage as an mp3 under uploads/. Returns (rel_path, error)."""
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    filename = secure_filename(file_storage.filename or '')
    if not filename.lower().endswith('.mp3'):
        return None, 'Only .mp3 files are accepted'

    stem = filename[:-4]
    ext = '.mp3'
    candidate = filename
    n = 1
    while os.path.exists(os.path.join(UPLOAD_DIR, candidate)):
        candidate = f'{stem} ({n}){ext}'
        n += 1

    dest = os.path.join(UPLOAD_DIR, candidate)
    file_storage.save(dest)
    return to_repo_relative(dest), None


def test_play(audio_rel_path, volume):
    audio_path = resolve_audio_path(audio_rel_path)
    if audio_path is None:
        return False, 'Not an allowed audio file'

    play_script = os.path.join(ROOT_DIR, 'playAzaan.sh')
    with _play_lock:
        stop_play()
        proc = subprocess.Popen(
            [play_script, str(audio_path), str(volume)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        _current_play['proc'] = proc
    return True, None


def stop_play():
    proc = _current_play.get('proc')
    if proc is not None and proc.poll() is None:
        proc.terminate()
    _current_play['proc'] = None


def is_playing():
    proc = _current_play.get('proc')
    return proc is not None and proc.poll() is None
