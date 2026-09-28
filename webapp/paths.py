"""Shared, allow-listed path resolution for anything a client can name (audio files, mawaqit files)."""

from pathlib import Path

from webapp.config import ROOT_DIR, UPLOAD_DIR, MAWAQIT_DIR


def resolve_audio_path(user_value):
    """Resolve a client-supplied audio path to a Path, or None if it's not allowed.

    Only accepts .mp3 files that live directly under the repo root (bundled Adhan-*.mp3)
    or under the uploads/ directory. Rejects anything that escapes those roots (path
    traversal) or that isn't an existing .mp3 file.
    """
    if not user_value:
        return None
    try:
        candidate = (Path(ROOT_DIR) / user_value).resolve()
    except (OSError, ValueError):
        return None

    allowed_roots = [Path(ROOT_DIR).resolve(), Path(UPLOAD_DIR).resolve()]
    if not any(candidate == root or root in candidate.parents for root in allowed_roots):
        return None
    if candidate.suffix.lower() != '.mp3' or not candidate.is_file():
        return None
    return candidate


def resolve_mawaqit_path(user_value):
    """Resolve a client-supplied mawaqit calendar JSON path, or None if it's not allowed.

    Accepts .json files under the repo root or under mawaqit_files/.
    """
    if not user_value:
        return None
    try:
        candidate = (Path(ROOT_DIR) / user_value).resolve()
    except (OSError, ValueError):
        return None

    allowed_roots = [Path(ROOT_DIR).resolve(), Path(MAWAQIT_DIR).resolve()]
    if not any(candidate == root or root in candidate.parents for root in allowed_roots):
        return None
    if candidate.suffix.lower() != '.json' or not candidate.is_file():
        return None
    return candidate


def to_repo_relative(path):
    """Render a Path as relative-to-repo-root when possible, for storing in settings.json."""
    path = Path(path)
    try:
        return str(path.relative_to(Path(ROOT_DIR).resolve()))
    except ValueError:
        return str(path)
