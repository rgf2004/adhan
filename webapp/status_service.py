"""Read-only status: installed cron jobs, today's prayer times, log tail."""

import getpass
import os
import shlex

from crontab import CronTab
from praytimes import PrayTimes

from updateAzaanTimers import compute_prayer_times
from webapp.config import CRON_COMMENT


def classify_job(job):
    cmd = job.command
    if 'playAzaan.sh' in cmd:
        kind = 'prayer'
        try:
            parts = shlex.split(cmd.split('>>')[0])
            audio_path, volume = parts[-2], parts[-1]
        except (ValueError, IndexError):
            audio_path, volume = None, None
    elif 'updateAzaanTimers.py' in cmd:
        kind = 'nightly-update'
        audio_path, volume = None, None
    elif 'truncate' in cmd:
        kind = 'monthly-log-clear'
        audio_path, volume = None, None
    else:
        kind = 'unknown'
        audio_path, volume = None, None

    return {
        'kind': kind,
        'schedule': f'{job.minute} {job.hour} {job.day} {job.month} {job.dow}',
        'command': cmd,
        'audio_path': audio_path,
        'volume': volume,
        'raw': str(job),
    }


def list_cron_jobs():
    tab = CronTab(user=getpass.getuser())
    jobs = [classify_job(j) for j in tab.find_comment(CRON_COMMENT)]

    order = {'prayer': 0, 'nightly-update': 1, 'monthly-log-clear': 2, 'unknown': 3}
    jobs.sort(key=lambda j: (order.get(j['kind'], 9), j['schedule']))
    return jobs


def compute_today_times(general):
    """Best-effort: returns (times_dict, error_message). Never raises/exits."""
    try:
        pt = PrayTimes()
        return compute_prayer_times(general, pt), None
    except SystemExit:
        return None, 'Could not compute prayer times with the current settings (see Settings page).'
    except Exception as e:
        return None, str(e)


def read_log_tail(path, max_lines=200, max_bytes=2_000_000):
    if not os.path.exists(path):
        return []
    size = os.path.getsize(path)
    with open(path, 'rb') as f:
        if size > max_bytes:
            f.seek(-max_bytes, os.SEEK_END)
        data = f.read()
    lines = data.decode('utf-8', errors='replace').splitlines()
    return lines[-max_lines:]
