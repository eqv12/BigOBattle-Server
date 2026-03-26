# server/webapp/app.py

import datetime
import os
import shutil
import zipfile
from server.logic import matchmaker
from flask import Flask, request, jsonify, render_template # type: ignore


# --- Project-specific imports ---
# These imports assume you run this from the project root with `python -m server.webapp.app`
from server import config
from server.database import db_handler
from server.games.catalog import get_game, list_games

# 1. Initialize the Flask Application
app = Flask(__name__)
db_handler.ensure_room_schema()
_match_queue = None
_room_matchmaking_tick = 0


def _ensure_match_queue():
    global _match_queue
    if _match_queue is None:
        _match_queue = matchmaker.start_matchmaker()
    return _match_queue


def _extract_bot_zip(file_storage, destination_path):
    """Extract a submitted ZIP into destination_path and normalize single-root zips."""
    if os.path.exists(destination_path):
        shutil.rmtree(destination_path)
    os.makedirs(destination_path, exist_ok=True)

    temp_extract_path = os.path.join(destination_path, "temp_extraction")
    os.makedirs(temp_extract_path, exist_ok=True)

    try:
        with zipfile.ZipFile(file_storage, 'r') as zip_ref:
            zip_ref.extractall(temp_extract_path)

        extracted_items = os.listdir(temp_extract_path)
        if len(extracted_items) == 1 and os.path.isdir(os.path.join(temp_extract_path, extracted_items[0])):
            root_folder = os.path.join(temp_extract_path, extracted_items[0])
            for item in os.listdir(root_folder):
                shutil.move(os.path.join(root_folder, item), destination_path)
        else:
            for item in extracted_items:
                shutil.move(os.path.join(temp_extract_path, item), destination_path)
    finally:
        if os.path.exists(temp_extract_path):
            shutil.rmtree(temp_extract_path)


def _parse_db_datetime(value):
    if not value:
        return None
    for fmt in ('%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S'):
        try:
            return datetime.datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def _pick_room_pair(room_id):
    global _room_matchmaking_tick
    _room_matchmaking_tick += 1
    return matchmaker.pick_room_pair(room_id, _room_matchmaking_tick, use_info=True)

# --- Web Routes (API Endpoints) ---

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/rooms', methods=['POST'])
def create_room():
    payload = request.get_json(silent=True) or {}
    game_key = str(payload.get('game_key', 'tron')).strip().lower()
    if not game_key:
        return jsonify({'error': 'game_key is required'}), 400

    room = db_handler.create_room(game_key)
    return jsonify({
        'room_code': room['room_code'],
        'admin_password': room['admin_password'],
        'game_key': room['game_key'],
    }), 201


@app.route('/api/games', methods=['GET'])
def get_games():
    return jsonify(list_games()), 200


@app.route('/api/games/<game_key>', methods=['GET'])
def get_game_details(game_key):
    game = get_game(game_key)
    if not game:
        return jsonify({'error': 'Unknown game'}), 404
    return jsonify(game), 200


@app.route('/api/rooms/<room_code>/join', methods=['POST'])
def join_room(room_code):
    room = db_handler.get_room_by_code(room_code)
    if not room:
        return jsonify({'error': 'Room not found'}), 404

    payload = request.get_json(silent=True) or {}
    display_name = str(payload.get('display_name', '')).strip()
    if not display_name:
        return jsonify({'error': 'display_name is required'}), 400

    participant, created = db_handler.get_or_create_participant(room['id'], display_name)
    return jsonify({
        'participant_id': participant['id'],
        'display_name': participant['display_name'],
        'created': created,
        'room_code': room['room_code'],
        'game_key': room['game_key'],
    }), 200


@app.route('/api/rooms/<room_code>/submit', methods=['POST'])
def submit_room_bot(room_code):
    room = db_handler.get_room_by_code(room_code)
    if not room:
        return jsonify({'error': 'Room not found'}), 404

    display_name = str(request.form.get('display_name', '')).strip()
    password = str(request.form.get('password', '')).strip()
    if not display_name:
        return jsonify({'error': 'Missing display_name in form data'}), 400
    if not password:
        return jsonify({'error': 'Missing password in form data'}), 400
    if 'bot_zip_file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400

    participant, _ = db_handler.get_or_create_participant(room['id'], display_name)

    # Submission rate-limit per participant
    last_sub_time = _parse_db_datetime(participant.get('last_submission_at'))
    if last_sub_time:
        delta = datetime.datetime.now() - last_sub_time
        limit_seconds = config.SUBMISSION_RATE_LIMIT_MINUTES * 60
        if delta.total_seconds() < limit_seconds:
            wait_time = int(limit_seconds - delta.total_seconds())
            return jsonify({'error': f'Rate limit exceeded. Please wait {wait_time} more seconds.'}), 429

    is_valid, is_first_set = db_handler.set_or_verify_participant_password(participant['id'], password)
    if not is_valid:
        return jsonify({'error': 'Authentication failed: Invalid password for this display_name'}), 401

    file = request.files['bot_zip_file']
    if file.filename == '':
        return jsonify({'error': 'No file selected for uploading'}), 400

    destination_path = os.path.join(config.ROOM_BOTS_DIR, room_code, display_name)
    try:
        _extract_bot_zip(file, destination_path)
    except zipfile.BadZipFile:
        return jsonify({'error': 'Invalid file format. Please upload a ZIP file.'}), 400

    run_script_path = os.path.join(destination_path, 'run.sh').replace('\\', '/')
    if not os.path.exists(run_script_path):
        return jsonify({'error': "Missing required file 'run.sh' in submitted ZIP"}), 400

    db_handler.update_participant_bot_path(participant['id'], run_script_path)

    # Ensure workers/scheduler are running and nudge one immediate scheduling pass.
    _ensure_match_queue()
    nudge_result = matchmaker.schedule_room_once(
        room_id=room['id'],
        room_code=room['room_code'],
        game_key=room['game_key'],
        tick_counter=1,
        reason='submit',
    )

    return jsonify({
        'message': f'Bot for {display_name} uploaded successfully',
        'room_code': room_code,
        'display_name': display_name,
        'password_initialized': is_first_set,
        'ranked_queue_nudge': nudge_result,
    }), 200


@app.route('/api/rooms/<room_code>/leaderboard', methods=['GET'])
def get_room_leaderboard(room_code):
    room = db_handler.get_room_by_code(room_code)
    if not room:
        return jsonify({'error': 'Room not found'}), 404

    rows = db_handler.get_room_leaderboard(room['id'], limit=100)
    data = []
    for rank, row in enumerate(rows, 1):
        data.append({
            'rank': rank,
            'display_name': row['display_name'],
            'rating': int(row['rating']),
            'rd': int(row['rd']),
            'matches_played': row['matches_played'],
        })
    return jsonify(data), 200


@app.route('/api/rooms/<room_code>/matches/recent', methods=['GET'])
def get_room_recent_matches(room_code):
    room = db_handler.get_room_by_code(room_code)
    if not room:
        return jsonify({'error': 'Room not found'}), 404

    limit = request.args.get('limit', default=20, type=int)
    limit = max(1, min(limit, 100))
    matches = db_handler.get_recent_room_matches(room['id'], limit=limit)
    return jsonify(matches), 200


@app.route('/api/rooms/<room_code>/matches/<int:match_id>/replay', methods=['GET'])
def get_room_match_replay(room_code, match_id):
    room = db_handler.get_room_by_code(room_code)
    if not room:
        return jsonify({'error': 'Room not found'}), 404

    replay_payload = db_handler.get_room_match_replay(room['id'], match_id)
    if not replay_payload:
        return jsonify({'error': 'Replay not found'}), 404
    return jsonify(replay_payload), 200


@app.route('/api/rooms/<room_code>/matches/<int:match_id>/raw-output', methods=['GET'])
def get_room_match_raw_output(room_code, match_id):
    room = db_handler.get_room_by_code(room_code)
    if not room:
        return jsonify({'error': 'Room not found'}), 404

    payload = db_handler.get_room_match_raw_output(room['id'], match_id)
    if not payload:
        return jsonify({'error': 'Raw output not found'}), 404
    return jsonify(payload), 200


@app.route('/api/rooms/<room_code>/test', methods=['POST'])
def test_room_bot(room_code):
    room = db_handler.get_room_by_code(room_code)
    if not room:
        return jsonify({'error': 'Room not found'}), 404

    if 'bot_zip_file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    tier = str(request.form.get('tier', 'tier1')).strip().lower()
    file = request.files['bot_zip_file']

    test_id = os.urandom(8).hex()
    test_dir = os.path.join(config.ROOM_BOTS_DIR, 'test_jobs', test_id)
    os.makedirs(test_dir, exist_ok=True)

    try:
        _extract_bot_zip(file, test_dir)
        user_bot_path = os.path.join(test_dir, 'run.sh').replace('\\', '/')

        if not os.path.exists(user_bot_path):
            shutil.rmtree(test_dir, ignore_errors=True)
            return jsonify({'error': "Missing required file 'run.sh' in submitted ZIP"}), 400

        benchmark_path = os.path.join(
            'bots_official', 'games', room['game_key'], 'benchmarks', tier, 'run.sh'
        ).replace('\\', '/')

        if not os.path.exists(benchmark_path):
            shutil.rmtree(test_dir, ignore_errors=True)
            return jsonify({'error': f'Benchmark bot not found for {room["game_key"]}:{tier}'}), 400

        queue = _ensure_match_queue()
        job_id = queue.enqueue_test({
            'job_id': test_id,
            'queue_type': 'test',
            'room_code': room_code,
            'room_id': room['id'],
            'game_key': room['game_key'],
            'tier': tier,
            'test_dir': test_dir,
            'user_bot_path': user_bot_path,
            'benchmark_path': benchmark_path,
        })

        return jsonify({
            'status': 'queued',
            'job_id': job_id,
            'room_code': room_code,
            'game_key': room['game_key'],
            'tier': tier,
            'status_url': f'/api/rooms/{room_code}/test-jobs/{job_id}',
        }), 202
    except zipfile.BadZipFile:
        shutil.rmtree(test_dir, ignore_errors=True)
        return jsonify({'error': 'Invalid file format. Please upload a ZIP file.'}), 400


@app.route('/api/rooms/<room_code>/test-jobs/<job_id>', methods=['GET'])
def get_test_job_status(room_code, job_id):
    room = db_handler.get_room_by_code(room_code)
    if not room:
        return jsonify({'error': 'Room not found'}), 404

    payload = matchmaker.get_test_job(job_id)
    if not payload:
        return jsonify({'error': 'Job not found'}), 404

    if payload.get('room_code') != room_code:
        return jsonify({'error': 'Job not found in this room'}), 404

    return jsonify(payload), 200


@app.route('/api/rooms/<room_code>/queue-match', methods=['POST'])
def queue_room_match(room_code):
    room = db_handler.get_room_by_code(room_code)
    if not room:
        return jsonify({'error': 'Room not found'}), 404

    payload = request.get_json(silent=True) or {}
    participant_a_id = payload.get('participant_a_id')
    participant_b_id = payload.get('participant_b_id')

    if participant_a_id is None or participant_b_id is None:
        pair = _pick_room_pair(room['id'])
        if not pair:
            return jsonify({'error': 'Need at least two participants with uploaded bots to queue a match'}), 400
        p0, p1 = pair
        participant_a_id = p0['id']
        participant_b_id = p1['id']

    p0 = db_handler.get_room_participant_by_id(int(participant_a_id))
    p1 = db_handler.get_room_participant_by_id(int(participant_b_id))
    if not p0 or not p1 or p0['room_id'] != room['id'] or p1['room_id'] != room['id']:
        return jsonify({'error': 'Invalid participant ids for this room'}), 400
    if not p0.get('active_bot_path') or not p1.get('active_bot_path'):
        return jsonify({'error': 'Both participants must have submitted bots before queueing a match'}), 400

    queue = _ensure_match_queue()
    queue.enqueue_ranked({
        'queue_type': 'room',
        'room_id': room['id'],
        'room_code': room_code,
        'game_key': room['game_key'],
        'participant_a_id': int(participant_a_id),
        'participant_b_id': int(participant_b_id),
        'participant_a_submission_version': int(p0.get('submission_version', 0)),
        'participant_b_submission_version': int(p1.get('submission_version', 0)),
        'is_ranked': True,
    })

    return jsonify({
        'status': 'queued',
        'room_code': room_code,
        'game_key': room['game_key'],
        'participant_a_id': int(participant_a_id),
        'participant_b_id': int(participant_b_id),
    }), 202

@app.route('/submit', methods=['POST'])
@app.route('/leaderboard', methods=['GET'])
@app.route('/test', methods=['POST'])
def legacy_endpoint_removed():
    return jsonify({
        'error': 'Legacy endpoint removed. Use room-first APIs under /api/rooms/*'
    }), 410


# --- This block allows you to run the server directly ---
if __name__ == '__main__':
    # debug=True allows the server to auto-reload when you save changes.
    # host='0.0.0.0' makes the server accessible from other computers on your network.
    app.run(host='0.0.0.0', port=5000, debug=True)