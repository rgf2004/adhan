"""Sync wrappers around mawaqit_util's async mosque search/generate functions.

Credentials are never persisted -- they live only for the duration of a single request.
"""

import asyncio
import os
import re

from mawaqit_util import cmd_nearby, cmd_search, cmd_generate

from webapp.config import MAWAQIT_DIR
from webapp.paths import to_repo_relative


def nearby(username, password, lat, lng):
    return asyncio.run(cmd_nearby(username, password, lat, lng))


def search(username, password, keyword):
    return asyncio.run(cmd_search(username, password, keyword))


def _slugify(name):
    slug = re.sub(r'[^a-zA-Z0-9]+', '-', name or 'mosque').strip('-').lower()
    return slug or 'mosque'


def generate(username, password, uuid, mosque_name=None):
    os.makedirs(MAWAQIT_DIR, exist_ok=True)
    filename = f'{_slugify(mosque_name)}-{uuid[:8]}.json'
    output_path = os.path.join(MAWAQIT_DIR, filename)
    asyncio.run(cmd_generate(username, password, uuid, output_path))
    return to_repo_relative(output_path)
