#!/usr/bin/env python3
"""Admin web app for the Adhan Clock. LAN-only, no login -- see README security notes."""

import os
import sys
from os.path import dirname, abspath

sys.path.insert(0, dirname(dirname(abspath(__file__))))

from flask import Flask, render_template, request, redirect, url_for, jsonify

from webapp import audio_service, mawaqit_service, settings_service, status_service
from webapp.config import METHODS, PRAYER_KEYS, SETTINGS_PATH


def create_app():
    app = Flask(__name__)
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB upload cap

    @app.route('/')
    def status_view():
        settings = settings_service.load_settings()
        general = settings.get('general', {})
        times, times_error = status_service.compute_today_times(general)
        cron_jobs = status_service.list_cron_jobs()
        log_path = general.get('log_file', 'adhan.log')
        if not os.path.isabs(log_path):
            log_path = os.path.join(dirname(dirname(abspath(__file__))), log_path)
        log_lines = status_service.read_log_tail(log_path)
        return render_template(
            'status.html',
            times=times, times_error=times_error,
            cron_jobs=cron_jobs, log_lines=log_lines,
            mode=general.get('mode', 'calculated'),
        )

    @app.route('/settings', methods=['GET', 'POST'])
    def settings_view():
        if request.method == 'GET':
            settings = settings_service.load_settings()
            return render_template(
                'settings.html', settings=settings, methods=METHODS,
                prayer_keys=PRAYER_KEYS, audio_files=audio_service.list_audio_files(),
                error=None, apply_output=None,
            )

        with settings_service._lock:
            previous = settings_service.load_settings()
            new_settings, errors = settings_service.form_to_settings(request.form, previous)
            if errors:
                return render_template(
                    'settings.html', settings=new_settings, methods=METHODS,
                    prayer_keys=PRAYER_KEYS, audio_files=audio_service.list_audio_files(),
                    error='\n'.join(errors), apply_output=None,
                ), 422

            settings_service.save_settings_atomic(new_settings)
            result = settings_service.apply_settings()

        if result.returncode != 0:
            error = (result.stdout + '\n' + result.stderr).strip()
            return render_template(
                'settings.html', settings=new_settings, methods=METHODS,
                prayer_keys=PRAYER_KEYS, audio_files=audio_service.list_audio_files(),
                error=error, apply_output=None,
            ), 422

        return redirect(url_for('status_view'))

    @app.route('/audio')
    def audio_view():
        return render_template(
            'audio.html', audio_files=audio_service.list_audio_files(),
            is_playing=audio_service.is_playing(), error=None,
        )

    @app.route('/audio/upload', methods=['POST'])
    def audio_upload():
        file_storage = request.files.get('file')
        if file_storage is None or not file_storage.filename:
            return render_template(
                'audio.html', audio_files=audio_service.list_audio_files(),
                is_playing=audio_service.is_playing(), error='No file selected',
            ), 400

        rel_path, error = audio_service.save_upload(file_storage)
        if error:
            return render_template(
                'audio.html', audio_files=audio_service.list_audio_files(),
                is_playing=audio_service.is_playing(), error=error,
            ), 400
        return redirect(url_for('audio_view'))

    @app.route('/audio/test-play', methods=['POST'])
    def audio_test_play():
        data = request.get_json(silent=True) or request.form
        path = data.get('path')
        volume = data.get('volume', 100)
        ok, error = audio_service.test_play(path, volume)
        if not ok:
            return jsonify({'status': 'error', 'error': error}), 400
        return jsonify({'status': 'playing'}), 202

    @app.route('/audio/stop', methods=['POST'])
    def audio_stop():
        audio_service.stop_play()
        return jsonify({'status': 'stopped'})

    @app.route('/mawaqit', methods=['GET'])
    def mawaqit_view():
        return render_template('mawaqit.html', results=None, action=None, error=None)

    @app.route('/mawaqit/nearby', methods=['POST'])
    def mawaqit_nearby():
        f = request.form
        try:
            mosques = mawaqit_service.nearby(f['username'], f['password'], float(f['lat']), float(f['lng']))
            return render_template('mawaqit.html', results=mosques, action='nearby', error=None)
        except Exception as e:
            return render_template('mawaqit.html', results=None, action='nearby', error=str(e)), 400

    @app.route('/mawaqit/search', methods=['POST'])
    def mawaqit_search():
        f = request.form
        try:
            mosques = mawaqit_service.search(f['username'], f['password'], f['keyword'])
            return render_template('mawaqit.html', results=mosques, action='search', error=None)
        except Exception as e:
            return render_template('mawaqit.html', results=None, action='search', error=str(e)), 400

    @app.route('/mawaqit/generate', methods=['POST'])
    def mawaqit_generate():
        f = request.form
        try:
            rel_path = mawaqit_service.generate(f['username'], f['password'], f['uuid'], f.get('mosque_name'))
            return render_template(
                'mawaqit.html', results=None, action='generate', error=None,
                generated_path=rel_path,
            )
        except Exception as e:
            return render_template('mawaqit.html', results=None, action='generate', error=str(e)), 400

    return app


app = create_app()

if __name__ == '__main__':
    host = os.environ.get('ADHAN_HOST', '0.0.0.0')
    port = int(os.environ.get('ADHAN_PORT', '8080'))
    app.run(host=host, port=port, debug=False, threaded=True)
