"""Redis-backed matchmaking workers and room pair selection helpers."""

import json
import math
import multiprocessing
import os
import shutil
import time

import redis  # type: ignore

from server import config
from server.database import db_handler
from server.logic import engine, rating_system


RD_SCALE = 173.7178  # 400 / ln(10)

_STARTED = False
_WORKER_PROCESSES = []
_QUEUE_GATEWAY = None
_SCHEDULER_PROCESS = None


def _g(phi):
    return 1.0 / math.sqrt(1.0 + 3.0 * phi * phi / (math.pi**2))


def _mu(rating):
    return (float(rating) - 1500.0) / RD_SCALE


def _phi(rd):
    return float(rd) / RD_SCALE


def _info_gain(p_rating, o_rating, o_rd):
    mu_p = _mu(p_rating)
    mu_o = _mu(o_rating)
    g_o = _g(_phi(o_rd))
    x = -g_o * (mu_p - mu_o)
    try:
        expected = 1.0 / (1.0 + math.exp(x))
    except OverflowError:
        expected = 0.0 if x > 0 else 1.0
    return (g_o * g_o) * expected * (1.0 - expected)


def _redis_client(redis_url=None):
    return redis.Redis.from_url(redis_url or config.REDIS_URL, decode_responses=True)


def _test_job_key(job_id):
    return f"{config.REDIS_TEST_JOB_KEY_PREFIX}{job_id}"


def _room_lock_key(room_id):
    return f"emergent:room-lock:{room_id}"


def _room_tick_key(room_id):
    return f"emergent:room-tick:{room_id}"


def _next_room_tick(client, room_id):
    return int(client.incr(_room_tick_key(room_id)))


def _set_test_job_state(client, job_id, status, **fields):
    payload = {
        'job_id': str(job_id),
        'status': status,
        'updated_at': int(time.time()),
    }
    payload.update(fields)
    key = _test_job_key(job_id)
    client.set(key, json.dumps(payload), ex=config.REDIS_TEST_JOB_TTL_SECONDS)


def get_test_job(job_id):
    client = _redis_client()
    raw = client.get(_test_job_key(job_id))
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def _select_best_opponent_for_room_player(player, all_players, room_id, use_info=True):
    player_id = player['id']
    player_rating = float(player.get('rating', 1500.0))
    player_sub_ver = int(player.get('submission_version', 0))

    def _find_opponents(window_size):
        opps = []
        for opp in all_players:
            if opp['id'] == player_id:
                continue
            
            if window_size is not None:
                if abs(player_rating - float(opp.get('rating', 1500.0))) > window_size:
                    continue
                    
            if db_handler.have_room_participants_played_since_submission(room_id, player_id, opp['id']):
                # Rematch Caps: Applied purely to bot version versions.
                # Regardless of stable vs unstable, no bot learns indefinitely.
                rematch_cap = int(getattr(config, 'ROOM_MAX_REMATCHES_CALIBRATION', 5))
                
                played_count = db_handler.count_room_bot_pair_matches(
                    room_id,
                    player_id,
                    player_sub_ver,
                    int(opp['id']),
                    int(opp.get('submission_version', 0)),
                )
                if played_count >= rematch_cap:
                    continue
            opps.append(opp)
        return opps

    # Expand the search progressively until opponents are found
    potential_opponents = []
    base_window = int(getattr(config, 'MATCHMAKING_RATING_WINDOW', 200))
    windows_to_try = [base_window, base_window * 2, base_window * 3, base_window * 4, None]
    
    for window in windows_to_try:
        potential_opponents = _find_opponents(window)
        if potential_opponents:
            break

    if not potential_opponents:
        return None

    # Removed the 'calibrated_opponents' trap bucket entirely.
    # The Glicko Info Gain math inherently prefers Stable bots via the g(RD)^2 multiplier anyway.
    selection_pool = potential_opponents

    if not use_info:
        selection_pool.sort(key=lambda o: abs(float(o.get('rating', 1500.0)) - player_rating))
        return selection_pool[0]

    best = None
    best_score = -1.0
    eps = 1e-12
    for opp in selection_pool:
        opp_rating = float(opp.get('rating', 1500.0))
        opp_rd = float(opp.get('rd', config.DEFAULT_RD))
        info = _info_gain(player_rating, opp_rating, opp_rd)
        min_info = float(getattr(config, 'ROOM_INFO_GAIN_MIN', 0.0))
        if info < min_info:
            continue

        if best is None or info > best_score + eps:
            best = opp
            best_score = info
        elif abs(info - best_score) <= eps:
            if abs(opp_rating - player_rating) < abs(float(best.get('rating', 1500.0)) - player_rating):
                best = opp
                best_score = info
    return best

def pick_room_pair(room_id, tick_counter, use_info=True):
    """Pick a room match pair using calibration ratio plus max information gain."""
    participants = db_handler.get_matchable_room_participants(room_id)
    if len(participants) < 2:
        return None

    is_calibration_tick = (tick_counter % (config.MATCHMAKING_RATIO + 1)) != 0
    rd_threshold = float(getattr(config, 'ROOM_RD_STABLE_THRESHOLD', 80.0))
    
    if is_calibration_tick:
        candidate_players = [p for p in participants if float(p.get('rd', config.DEFAULT_RD)) > rd_threshold]
        if not candidate_players:
            candidate_players = participants
    else:
        candidate_players = [p for p in participants if float(p.get('rd', config.DEFAULT_RD)) <= rd_threshold]
        if not candidate_players:
            candidate_players = participants

    candidate_players.sort(key=lambda p: float(p.get('rd', config.DEFAULT_RD)), reverse=True)

    # Pick the FIRST candidate that successfully finds a valid opponent.
    # This guarantees high-RD (starved) players get priority.
    for player in candidate_players:
        opponent = _select_best_opponent_for_room_player(player, participants, room_id, use_info=use_info)
        if opponent:
            return (player, opponent)

    return None


def _enqueue_ranked_room_match(client, queue_gateway, room, tick_counter, reason='scheduler'):
    pair = pick_room_pair(room['id'], tick_counter, use_info=True)
    if not pair:
        return {'queued': False, 'reason': 'no_pair'}

    p0, p1 = pair
    lock_key = _room_lock_key(room['id'])
    lock_ttl = max(10, int(getattr(config, 'ROOM_SCHEDULER_LOCK_TTL_SECONDS', 45)))
    lock_set = client.set(lock_key, str(int(time.time())), nx=True, ex=lock_ttl)
    if not lock_set:
        return {'queued': False, 'reason': 'room_locked'}

    queue_gateway.enqueue_ranked({
        'queue_type': 'room',
        'room_id': room['id'],
        'room_code': room['room_code'],
        'game_key': room['game_key'],
        'participant_a_id': int(p0['id']),
        'participant_b_id': int(p1['id']),
        'participant_a_submission_version': int(p0.get('submission_version', 0)),
        'participant_b_submission_version': int(p1.get('submission_version', 0)),
        'is_ranked': True,
        'room_lock_key': lock_key,
        'scheduled_reason': reason,
    })

    return {
        'queued': True,
        'participant_a_id': int(p0['id']),
        'participant_b_id': int(p1['id']),
        'lock_key': lock_key,
    }


def schedule_room_once(room_id, room_code, game_key, tick_counter=1, reason='submit'):
    """Best-effort single-room scheduler nudge used after successful submissions."""
    client = _redis_client()
    queue_gateway = MatchQueueGateway(client)
    room = {
        'id': int(room_id),
        'room_code': room_code,
        'game_key': game_key,
    }
    return _enqueue_ranked_room_match(client, queue_gateway, room, tick_counter, reason=reason)


class MatchQueueGateway:
    """Queue facade used by web handlers and scripts."""

    def __init__(self, client):
        self.client = client

    def enqueue_ranked(self, job):
        self.client.lpush(config.REDIS_QUEUE_RANKED, json.dumps(job))

    def enqueue_test(self, job):
        job_id = str(job.get('job_id') or os.urandom(8).hex())
        job['job_id'] = job_id
        _set_test_job_state(
            self.client,
            job_id,
            'queued',
            room_code=job.get('room_code'),
            game_key=job.get('game_key'),
            tier=job.get('tier'),
        )
        self.client.lpush(config.REDIS_QUEUE_TEST, json.dumps(job))
        return job_id

    def put(self, match_request):
        """Compatibility method for legacy scripts that call queue.put({...})."""
        self.enqueue_ranked(match_request)


def _process_legacy_team_match(match_request, worker_name):
    team0_id = match_request['team_a_id']
    team1_id = match_request['team_b_id']
    print(f"[{worker_name}] Picked up match: Team {team0_id} vs Team {team1_id}")

    team0 = db_handler.get_team_by_id(team0_id)
    team1 = db_handler.get_team_by_id(team1_id)

    if not (team0 and team1 and team0['active_bot_path'] and team1['active_bot_path']):
        print(f"[{worker_name}] ERROR: Could not find one or both bots for match. Skipping.")
        return

    bot0_path = team0['active_bot_path']
    bot1_path = team1['active_bot_path']

    match_id = db_handler.create_match(team0_id, team1_id)
    print(f"[{worker_name}] Match created with ID: {match_id}")

    match_result = engine.run_match(bot0_path, bot1_path)
    winner_key = match_result['winner']
    replay_data = match_result['replay']

    rating_system.update_ratings(team0_id, team1_id, winner_key, rating_type='final')

    winner_team_id = None
    if winner_key == 'p0':
        winner_team_id = team0_id
    elif winner_key == 'p1':
        winner_team_id = team1_id

    termination_reason = match_result['termination_reason']
    db_handler.update_match_result(match_id, winner_team_id, replay_data=replay_data)
    db_handler.update_team_match_stats(team0_id, team1_id)

    print(f"[{worker_name}] Finished Match {match_id}: {termination_reason}. Waiting for next match.")


def _process_room_match(match_request, worker_name, client=None):
    lock_key = match_request.get('room_lock_key')
    room_id = match_request['room_id']
    participant_a_id = match_request['participant_a_id']
    participant_b_id = match_request['participant_b_id']
    expected_a_sub_ver = int(match_request.get('participant_a_submission_version', 0))
    expected_b_sub_ver = int(match_request.get('participant_b_submission_version', 0))

    room = db_handler.get_room_by_code(match_request['room_code']) if match_request.get('room_code') else None
    game_key = match_request.get('game_key') or (room['game_key'] if room else 'tron')

    print(
        f"[{worker_name}] Picked up room match: room={room_id}, "
        f"participants={participant_a_id} vs {participant_b_id}, game={game_key}"
    )

    try:
        p0 = db_handler.get_room_participant_by_id(participant_a_id)
        p1 = db_handler.get_room_participant_by_id(participant_b_id)
        if not (p0 and p1 and p0['active_bot_path'] and p1['active_bot_path']):
            print(f"[{worker_name}] ERROR: Invalid room participant bot paths. Skipping.")
            return

        # If either participant submitted a newer bot after queueing, drop this stale match job.
        current_a_ver = int(p0.get('submission_version', 0))
        current_b_ver = int(p1.get('submission_version', 0))
        if current_a_ver != expected_a_sub_ver or current_b_ver != expected_b_sub_ver:
            print(
                f"[{worker_name}] Skipping stale room match job for room={room_id}: "
                f"expected versions ({expected_a_sub_ver}, {expected_b_sub_ver}), "
                f"current ({current_a_ver}, {current_b_ver})"
            )
            return

        match_id = db_handler.create_room_match(room_id, game_key, participant_a_id, participant_b_id)
        match_result = engine.run_match(p0['active_bot_path'], p1['active_bot_path'])

        winner_key = match_result['winner']
        replay_data = match_result['replay']
        termination_reason = match_result['termination_reason']

        rating_system.update_room_ratings(room_id, participant_a_id, participant_b_id, winner_key)

        winner_participant_id = None
        if winner_key == 'p0':
            winner_participant_id = participant_a_id
        elif winner_key == 'p1':
            winner_participant_id = participant_b_id

        db_handler.update_room_match_result(match_id, winner_participant_id, replay_data, termination_reason)
        db_handler.update_room_match_stats(room_id, participant_a_id, participant_b_id)

        print(f"[{worker_name}] Finished room match {match_id}: {termination_reason}. Waiting for next match.")
    finally:
        if client and lock_key:
            client.delete(lock_key)

        # Chain schedule the next room match so progression does not depend solely on
        # the standalone scheduler process lifecycle.
        if client and room and getattr(config, 'ROOM_SCHEDULER_ENABLED', True):
            try:
                queue_gateway = MatchQueueGateway(client)
                tick_counter = _next_room_tick(client, room_id)
                next_result = _enqueue_ranked_room_match(
                    client,
                    queue_gateway,
                    room,
                    tick_counter=tick_counter,
                    reason='chain',
                )
                if next_result.get('queued'):
                    print(
                        f"[{worker_name}] Chained room queue: room={room['room_code']} "
                        f"p{next_result['participant_a_id']} vs p{next_result['participant_b_id']}"
                    )
            except Exception as exc:
                print(f"[{worker_name}] Failed to chain schedule next room match: {exc}")


def _process_test_match(match_request, worker_name, client):
    job_id = match_request['job_id']
    room_code = match_request['room_code']
    game_key = match_request['game_key']
    tier = match_request['tier']
    user_bot_path = match_request['user_bot_path']
    benchmark_path = match_request['benchmark_path']
    test_dir = match_request['test_dir']

    _set_test_job_state(client, job_id, 'running', room_code=room_code, game_key=game_key, tier=tier)

    print(f"[{worker_name}] Picked up test job {job_id}: room={room_code}, game={game_key}, tier={tier}")
    try:
        match_result = engine.run_match(user_bot_path, benchmark_path)
        replay = json.loads(match_result['replay'])

        _set_test_job_state(
            client,
            job_id,
            'success',
            room_code=room_code,
            game_key=game_key,
            tier=tier,
            winner=match_result['winner'],
            termination=match_result['termination_reason'],
            replay=replay,
            raw_output=replay.get('result', {}).get('bot_raw_outputs', {}),
        )
        print(f"[{worker_name}] Finished test job {job_id}")
    except Exception as exc:
        _set_test_job_state(
            client,
            job_id,
            'failed',
            room_code=room_code,
            game_key=game_key,
            tier=tier,
            error=str(exc),
        )
        print(f"[{worker_name}] Test job failed {job_id}: {exc}")
    finally:
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir, ignore_errors=True)


def run_ranked_worker(redis_url):
    worker_name = multiprocessing.current_process().name
    client = _redis_client(redis_url)
    print(f"[{worker_name}] Ranked worker started.")

    while True:
        try:
            item = client.brpop(config.REDIS_QUEUE_RANKED, timeout=5)
            if not item:
                continue

            _, payload = item
            match_request = json.loads(payload)
            queue_type = match_request.get('queue_type', 'legacy')
            if queue_type == 'room':
                _process_room_match(match_request, worker_name, client=client)
            else:
                _process_legacy_team_match(match_request, worker_name)
        except Exception as exc:
            print(f"[{worker_name}] FATAL ERROR processing ranked job: {exc}")
            time.sleep(1)


def run_room_scheduler(redis_url):
    worker_name = multiprocessing.current_process().name
    tick_seconds = max(1, int(getattr(config, 'ROOM_SCHEDULER_TICK_SECONDS', 5)))
    client = _redis_client(redis_url)
    queue_gateway = MatchQueueGateway(client)
    tick_counter = 0

    print(f"[{worker_name}] Room scheduler started. Tick every {tick_seconds}s")
    while True:
        tick_counter += 1
        try:
            rooms = db_handler.get_open_rooms()
            queued = 0
            skipped_locked = 0
            skipped_not_ready = 0
            skipped_no_pair = 0
            skipped_converged = 0

            for room in rooms:
                stats = db_handler.get_room_matchmaking_stats(room['id'])
                if stats['matchable_participants'] < 2:
                    skipped_not_ready += 1
                    continue

                convergence = db_handler.get_room_convergence_stats(room['id'])
                if convergence['is_converged']:
                    skipped_converged += 1
                    print(
                        f"[{worker_name}] Tick {tick_counter} room={room['room_code']} converged: "
                        f"max_rd={convergence['max_rd']:.2f} calibrating={convergence['calibrating_participants']}"
                    )
                    continue

                result = _enqueue_ranked_room_match(
                    client,
                    queue_gateway,
                    room,
                    tick_counter=_next_room_tick(client, room['id']),
                    reason='scheduler',
                )
                if result['queued']:
                    queued += 1
                    print(
                        f"[{worker_name}] Tick {tick_counter} queued room={room['room_code']} "
                        f"p{result['participant_a_id']} vs p{result['participant_b_id']} "
                        f"(matchable={stats['matchable_participants']}, "
                        f"calibrating={stats['calibrating_participants']}, "
                        f"calibrated={stats['calibrated_participants']})"
                    )
                elif result['reason'] == 'room_locked':
                    skipped_locked += 1
                else:
                    skipped_no_pair += 1

            print(
                f"[{worker_name}] Tick {tick_counter} summary: rooms={len(rooms)} "
                f"queued={queued} locked={skipped_locked} "
                f"not_ready={skipped_not_ready} converged={skipped_converged} no_pair={skipped_no_pair}"
            )
        except Exception as exc:
            print(f"[{worker_name}] FATAL ERROR in room scheduler tick {tick_counter}: {exc}")

        time.sleep(tick_seconds)


def run_test_worker(redis_url):
    worker_name = multiprocessing.current_process().name
    client = _redis_client(redis_url)
    print(f"[{worker_name}] Test worker started.")

    while True:
        try:
            item = client.brpop(config.REDIS_QUEUE_TEST, timeout=5)
            if not item:
                continue

            _, payload = item
            test_request = json.loads(payload)
            _process_test_match(test_request, worker_name, client)
        except Exception as exc:
            print(f"[{worker_name}] FATAL ERROR processing test job: {exc}")
            time.sleep(1)


def _spawn_worker(target, args):
    proc = multiprocessing.Process(target=target, args=args, daemon=True)
    proc.start()
    _WORKER_PROCESSES.append(proc)


def start_matchmaker():
    """Start Redis-backed dedicated worker pools for ranked and test queues."""
    global _STARTED, _QUEUE_GATEWAY, _SCHEDULER_PROCESS
    if _STARTED and _QUEUE_GATEWAY is not None:
        return _QUEUE_GATEWAY

    print("--- Starting Redis Matchmaking System ---")
    client = _redis_client()
    client.ping()

    ranked_count = max(1, int(getattr(config, 'RANKED_WORKER_PROCESSES', 1)))
    test_count = max(1, int(getattr(config, 'TEST_WORKER_PROCESSES', 1)))

    print(f"Creating {ranked_count} ranked workers and {test_count} test workers...")
    for _ in range(ranked_count):
        _spawn_worker(run_ranked_worker, (config.REDIS_URL,))
    for _ in range(test_count):
        _spawn_worker(run_test_worker, (config.REDIS_URL,))

    if getattr(config, 'ROOM_SCHEDULER_ENABLED', True):
        _SCHEDULER_PROCESS = multiprocessing.Process(
            target=run_room_scheduler,
            args=(config.REDIS_URL,),
            daemon=True,
        )
        _SCHEDULER_PROCESS.start()
        _WORKER_PROCESSES.append(_SCHEDULER_PROCESS)

    _QUEUE_GATEWAY = MatchQueueGateway(client)
    _STARTED = True
    print("Redis matchmaking system is running in the background.")
    return _QUEUE_GATEWAY
