import sys, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import flask
from flask import render_template, request, session, jsonify
import uuid
import string
import random
import json
import threading
from datetime import datetime, timedelta

zahlenraten = flask.Flask(__name__, template_folder="zahlenraten/templates")
zahlenraten.secret_key = "zahlenraten_secret_key_" + str(uuid.uuid4())
zahlenraten.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
zahlenraten.config['SESSION_COOKIE_SECURE'] = False

DATA_FILE = os.path.join(os.path.dirname(__file__), 'zahlenraten', 'game_data.json')
STATS_FILE = os.path.join(os.path.dirname(__file__), 'zahlenraten', 'request_stats.json')
GAME_STATS_FILE = os.path.join(os.path.dirname(__file__), 'zahlenraten', 'game_stats.json')

lobbies = {}
lobby_members = {}
lobby_spectators = {}
guest_names = {}
lobby_messages = {}
lobby_turn = {}
lobby_config = {}
player_stats = {}
lobby_round_winner = {}
request_stats = {}
game_stats = []


def load_player_stats():
    global player_stats
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                player_stats = data.get('players', {})
        except Exception as e:
            print(f"Error loading stats: {e}")
            player_stats = {}
    else:
        player_stats = {}

def save_player_stats():
    try:
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump({'players': player_stats}, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving stats: {e}")

load_player_stats()

def auto_save_stats():
    save_player_stats()
    threading.Timer(5.0, auto_save_stats).daemon = True
    threading.Timer(5.0, auto_save_stats).start()

auto_save_stats()

def load_request_stats():
    global request_stats
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                request_stats = data.get('requests', {})
        except Exception as e:
            print(f"Error loading request stats: {e}")
            request_stats = {}
    else:
        request_stats = {}

def save_request_stats():
    global request_stats
    if request_stats:
        try:
            os.makedirs(os.path.dirname(STATS_FILE), exist_ok=True)
            with open(STATS_FILE, 'w', encoding='utf-8') as f:
                json.dump({'requests': request_stats}, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving request stats: {e}")

def track_request(endpoint_name):
    global request_stats
    if endpoint_name not in request_stats:
        request_stats[endpoint_name] = 0
    request_stats[endpoint_name] += 1

def load_game_stats():
    global game_stats
    if os.path.exists(GAME_STATS_FILE):
        try:
            with open(GAME_STATS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                game_stats = data.get('games', [])
        except Exception as e:
            print(f"Error loading game stats: {e}")
            game_stats = []
    else:
        game_stats = []

def save_game_stats():
    global game_stats
    if game_stats:
        try:
            os.makedirs(os.path.dirname(GAME_STATS_FILE), exist_ok=True)
            with open(GAME_STATS_FILE, 'w', encoding='utf-8') as f:
                json.dump({'games': game_stats}, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving game stats: {e}")

load_request_stats()
load_game_stats()

def auto_save_request_stats():
    save_request_stats()
    threading.Timer(5.0, auto_save_request_stats).daemon = True
    threading.Timer(5.0, auto_save_request_stats).start()

auto_save_request_stats()

def cleanup_inactive_guests():
    global guest_names
    now = datetime.now()
    expired = [name for name, data in guest_names.items() 
               if (now - data['timestamp']).total_seconds() > 600]
    for name in expired:
        del guest_names[name]
    threading.Timer(60.0, cleanup_inactive_guests).daemon = True
    threading.Timer(60.0, cleanup_inactive_guests).start()

cleanup_inactive_guests()

def cleanup_expired_player_stats():
    global player_stats
    now = datetime.now()
    expired_player_ids = set()
    
    for player_id, stat_data in list(player_stats.items()):
        player_name = stat_data.get('name')
        if player_name:
            if player_name not in guest_names:
                expired_player_ids.add(player_id)
    
    for player_id in expired_player_ids:
        del player_stats[player_id]
    
    if expired_player_ids:
        save_player_stats()
    
    threading.Timer(300.0, cleanup_expired_player_stats).daemon = True
    threading.Timer(300.0, cleanup_expired_player_stats).start()

cleanup_expired_player_stats()

def generate_lobby_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))

def get_user_id():
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
    return session['user_id']

def get_guest_name_expiry(name):
    if name not in guest_names:
        return -1
    elapsed = (datetime.now() - guest_names[name]['timestamp']).total_seconds()
    remaining = max(0, 600 - elapsed)
    return int(remaining)

def update_user_timestamp(username):
    if username in guest_names:
        guest_names[username]['timestamp'] = datetime.now()

def remove_user_from_lobbies(user_id):
    global lobby_members, lobbies, lobby_turn, lobby_spectators
    
    for lobby_code in list(lobby_members.keys()):
        lobby_members[lobby_code] = [
            m for m in lobby_members[lobby_code]
            if m['player_id'] != user_id
        ]
        
        if lobby_code in lobby_spectators:
            lobby_spectators[lobby_code] = [
                p for p in lobby_spectators[lobby_code]
                if p != user_id
            ]
        
        if not lobby_members[lobby_code] and (lobby_code not in lobby_spectators or not lobby_spectators[lobby_code]):
            del lobbies[lobby_code]
            del lobby_members[lobby_code]
            if lobby_code in lobby_messages:
                del lobby_messages[lobby_code]
            if lobby_code in lobby_turn:
                del lobby_turn[lobby_code]
            if lobby_code in lobby_spectators:
                del lobby_spectators[lobby_code]

@zahlenraten.route("/")
def home():
    try:
        import wsgi as wsgi_mod
        footer = getattr(wsgi_mod, "FOOTER", "")
    except Exception:
        footer = ""
    return render_template("home.html", footer=footer)

@zahlenraten.route('/api/health', methods=['GET'])
def api_health():
    return jsonify({'status': 'ok'})

@zahlenraten.route('/api/stats-summary', methods=['GET'])
def api_stats_summary():
    total_requests = sum(request_stats.values())
    return jsonify({
        'success': True,
        'total_requests': total_requests,
        'games_played': len(game_stats),
        'requests_by_endpoint': request_stats
    })

@zahlenraten.route('/api/session-status', methods=['GET'])
def api_session_status():
    track_request('session_status')
    user_id = get_user_id()
    
    if 'username' not in session:
        return jsonify({'success': True, 'logged_in': False})
    
    username = session.get('username')
    
    if username not in guest_names or guest_names[username]['user_id'] != user_id:
        return jsonify({'success': True, 'logged_in': False})
    
    current_lobby = None
    for lobby_code, members in lobby_members.items():
        if any(m['player_id'] == user_id for m in members):
            current_lobby = lobby_code
            break
    
    return jsonify({
        'success': True,
        'logged_in': True,
        'user_id': user_id,
        'username': username,
        'lobby_code': current_lobby
    })

@zahlenraten.route('/api/logout', methods=['POST'])
def api_logout():
    track_request('logout')
    
    if 'username' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    username = session.get('username')
    user_id = get_user_id()
    
    remove_user_from_lobbies(user_id)
    
    if username in guest_names and guest_names[username]['user_id'] == user_id:
        del guest_names[username]
    
    session.clear()
    
    return jsonify({'success': True})

@zahlenraten.route('/api/check-name', methods=['POST'])
def api_check_name():
    track_request('check_name')
    data = request.get_json()
    name = data.get('name', '').strip()
    
    if not name or len(name) > 30:
        return jsonify({'success': False, 'available': False, 'error': 'Invalid name'}), 400
    
    if name in guest_names:
        expiry = get_guest_name_expiry(name)
        return jsonify({
            'success': True,
            'available': False,
            'expires_in': expiry
        })
    
    return jsonify({'success': True, 'available': True})

@zahlenraten.route('/api/login', methods=['POST'])
def api_login():
    track_request('login')
    data = request.get_json()
    name = data.get('name', '').strip()
    
    if not name or len(name) > 30:
        return jsonify({'success': False, 'error': 'Invalid name'}), 400
    
    user_id = get_user_id()
    
    if name in guest_names:
        expiry = get_guest_name_expiry(name)
        if expiry > 0:
            return jsonify({'success': False, 'error': 'Name already in use'}), 409
        else:
            old_user_id = guest_names[name]['user_id']
            remove_user_from_lobbies(old_user_id)
    
    session['username'] = name
    session.permanent = True
    
    guest_names[name] = {
        'user_id': user_id,
        'timestamp': datetime.now()
    }
    
    if user_id not in player_stats:
        player_stats[user_id] = {'name': name, 'wins': 0}
    
    return jsonify({'success': True, 'user_id': user_id, 'username': name})

@zahlenraten.route('/api/create-lobby', methods=['POST'])
def api_create_lobby():
    track_request('create_lobby')
    if 'username' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    update_user_timestamp(session['username'])
    
    data = request.get_json()
    min_range = data.get('min_range', 1)
    max_range = data.get('max_range', 100)
    max_players = data.get('max_players', 10)
    
    if min_range < 1 or max_range < min_range or max_range > 1000:
        return jsonify({'success': False, 'error': 'Invalid range'}), 400
    
    if max_players < 2 or max_players > 100:
        return jsonify({'success': False, 'error': 'Invalid player count'}), 400
    
    user_id = get_user_id()
    lobby_id = str(uuid.uuid4())
    lobby_code = generate_lobby_code()
    
    while lobby_code in lobbies:
        lobby_code = generate_lobby_code()
    
    lobbies[lobby_code] = {
        'id': lobby_id,
        'code': lobby_code,
        'host_id': user_id,
        'created_at': datetime.now(),
        'game_started': False,
        'secret_number': None,
        'min_range': min_range,
        'max_range': max_range,
        'max_players': max_players
    }
    
    lobby_members[lobby_code] = [{
        'player_id': user_id,
        'name': session['username'],
        'is_host': True
    }]
    
    lobby_messages[lobby_code] = []
    lobby_turn[lobby_code] = user_id
    
    return jsonify({
        'success': True,
        'lobby_code': lobby_code,
        'lobby_id': lobby_id
    })

@zahlenraten.route('/api/join-lobby', methods=['POST'])
def api_join_lobby():
    track_request('join_lobby')
    if 'username' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    update_user_timestamp(session['username'])
    
    data = request.get_json()
    lobby_code = data.get('code', '').strip().upper()
    
    if lobby_code not in lobbies:
        return jsonify({'success': False, 'error': 'Lobby not found'}), 404
    
    lobby = lobbies[lobby_code]
    members = lobby_members[lobby_code]
    user_id = get_user_id()
    
    if any(m['player_id'] == user_id for m in members):
        return jsonify({'success': True, 'lobby_code': lobby_code})
    
    if len(members) >= lobby['max_players']:
        return jsonify({'success': False, 'error': 'Lobby is full'}), 403
    
    if lobby['game_started']:
        if lobby_code not in lobby_spectators:
            lobby_spectators[lobby_code] = []
        if user_id not in lobby_spectators[lobby_code]:
            lobby_spectators[lobby_code].append(user_id)
        return jsonify({'success': True, 'lobby_code': lobby_code, 'spectator': True})
    
    members.append({
        'player_id': user_id,
        'name': session['username'],
        'is_host': False
    })
    
    return jsonify({'success': True, 'lobby_code': lobby_code})

@zahlenraten.route('/api/lobby-info/<lobby_code>', methods=['GET'])
def api_lobby_info(lobby_code):
    track_request('lobby_info')
    if 'username' in session:
        update_user_timestamp(session['username'])
    
    lobby_code = lobby_code.upper()
    
    if lobby_code not in lobbies:
        return jsonify({'success': False, 'error': 'Lobby not found'}), 404
    
    lobby = lobbies[lobby_code]
    members = lobby_members.get(lobby_code, [])
    current_turn_player = lobby_turn.get(lobby_code)
    user_id = get_user_id() if 'user_id' in session else None
    
    is_spectator = False
    if user_id and lobby_code in lobby_spectators:
        is_spectator = user_id in lobby_spectators[lobby_code]
    
    member_data = []
    for m in members:
        stats = player_stats.get(m['player_id'], {'wins': 0})
        member_data.append({
            'player_id': m['player_id'],
            'name': m['name'],
            'is_host': m['is_host'],
            'wins': stats.get('wins', 0)
        })
    
    return jsonify({
        'success': True,
        'lobby_code': lobby_code,
        'members': member_data,
        'host_id': lobby['host_id'],
        'game_started': lobby['game_started'],
        'current_turn': current_turn_player,
        'min_range': lobby['min_range'],
        'max_range': lobby['max_range'],
        'max_players': lobby['max_players'],
        'messages': lobby_messages.get(lobby_code, []),
        'is_spectator': is_spectator
    })

@zahlenraten.route('/api/start-game/<lobby_code>', methods=['POST'])
def api_start_game(lobby_code):
    track_request('start_game')
    if 'username' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    update_user_timestamp(session['username'])
    
    lobby_code = lobby_code.upper()
    
    if lobby_code not in lobbies:
        return jsonify({'success': False, 'error': 'Lobby not found'}), 404
    
    lobby = lobbies[lobby_code]
    user_id = get_user_id()
    
    if lobby['host_id'] != user_id:
        return jsonify({'success': False, 'error': 'Only host can start game'}), 403
    
    lobby['game_started'] = True
    lobby['secret_number'] = random.randint(lobby['min_range'], lobby['max_range'])
    lobby_messages[lobby_code] = []
    lobby_round_winner[lobby_code] = None
    
    if lobby_code in lobby_members and lobby_members[lobby_code]:
        members = lobby_members[lobby_code].copy()
        random.shuffle(members)
        lobby_turn[lobby_code] = members[0]['player_id']
    
    return jsonify({'success': True})

@zahlenraten.route('/api/guess', methods=['POST'])
def api_guess():
    track_request('guess')
    if 'username' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    update_user_timestamp(session['username'])
    
    data = request.get_json()
    lobby_code = data.get('lobby_code', '').upper()
    guess_val = data.get('guess', 0)
    
    if lobby_code not in lobbies:
        return jsonify({'success': False, 'error': 'Lobby not found'}), 404
    
    lobby = lobbies[lobby_code]
    user_id = get_user_id()
    
    if lobby_turn.get(lobby_code) != user_id:
        return jsonify({'success': False, 'error': 'Not your turn'}), 403
    
    if not lobby['game_started'] or lobby['secret_number'] is None:
        return jsonify({'success': False, 'error': 'Game not started'}), 400
    
    messages = lobby_messages.get(lobby_code, [])
    if messages and messages[-1]['result'] == 'correct':
        return jsonify({'success': False, 'error': 'Game already won, wait for next round'}), 400
    
    secret = lobby['secret_number']
    username = session.get('username', 'Unknown')
    
    if guess_val == secret:
        result = 'correct'
        if lobby_code not in lobby_round_winner or lobby_round_winner[lobby_code] is None:
            lobby_round_winner[lobby_code] = user_id
            if user_id not in player_stats:
                player_stats[user_id] = {'name': username, 'wins': 0}
            player_stats[user_id]['wins'] += 1
            save_player_stats()
            
            game_stat = {
                'player_count': len(lobby_members.get(lobby_code, [])),
                'guess_range': f"{lobby['min_range']}-{lobby['max_range']}",
                'correct_guess': guess_val,
                'max_players': lobby['max_players'],
                'timestamp': datetime.now().isoformat()
            }
            game_stats.append(game_stat)
            save_game_stats()
    elif guess_val < secret:
        result = 'low'
    else:
        result = 'high'
    
    message = {
        'player': username,
        'guess': guess_val,
        'result': result
    }
    lobby_messages[lobby_code].append(message)
    
    if result != 'correct':
        members = lobby_members[lobby_code]
        current_index = next((i for i, m in enumerate(members) 
                             if m['player_id'] == user_id), -1)
        next_index = (current_index + 1) % len(members)
        lobby_turn[lobby_code] = members[next_index]['player_id']
    
    return jsonify({
        'success': True,
        'result': result,
        'correct_number': secret if result == 'correct' else None
    })

@zahlenraten.route('/api/reset-game/<lobby_code>', methods=['POST'])
def api_reset_game(lobby_code):
    track_request('reset_game')
    if 'username' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    update_user_timestamp(session['username'])
    
    lobby_code = lobby_code.upper()
    
    if lobby_code not in lobbies:
        return jsonify({'success': False, 'error': 'Lobby not found'}), 404
    
    lobby = lobbies[lobby_code]
    user_id = get_user_id()
    
    if lobby['host_id'] != user_id:
        return jsonify({'success': False, 'error': 'Only host can reset'}), 403
    
    lobby['game_started'] = False
    lobby['secret_number'] = None
    lobby_messages[lobby_code] = []
    lobby_round_winner[lobby_code] = None
    
    members = lobby_members[lobby_code]
    if lobby_code in lobby_spectators:
        for spectator_id in lobby_spectators[lobby_code]:
            if len(members) < lobby['max_players']:
                spectator_name = 'Unknown'
                if spectator_id in player_stats:
                    spectator_name = player_stats[spectator_id].get('name', 'Unknown')
                
                members.append({
                    'player_id': spectator_id,
                    'name': spectator_name,
                    'is_host': False
                })
        
        del lobby_spectators[lobby_code]
    
    return jsonify({'success': True})

@zahlenraten.route('/api/transfer-host/<lobby_code>', methods=['POST'])
def api_transfer_host(lobby_code):
    track_request('transfer_host')
    if 'username' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    update_user_timestamp(session['username'])
    
    data = request.get_json()
    new_host_id = data.get('player_id')
    
    lobby_code = lobby_code.upper()
    
    if lobby_code not in lobbies:
        return jsonify({'success': False, 'error': 'Lobby not found'}), 404
    
    lobby = lobbies[lobby_code]
    user_id = get_user_id()
    
    if lobby['host_id'] != user_id:
        return jsonify({'success': False, 'error': 'Only host can transfer'}), 403
    
    members = lobby_members[lobby_code]
    if not any(m['player_id'] == new_host_id for m in members):
        return jsonify({'success': False, 'error': 'Player not in lobby'}), 404
    
    lobby['host_id'] = new_host_id
    for member in members:
        member['is_host'] = (member['player_id'] == new_host_id)
    
    return jsonify({'success': True})

@zahlenraten.route('/api/update-lobby-config/<lobby_code>', methods=['POST'])
def api_update_lobby_config(lobby_code):
    track_request('update_lobby_config')
    if 'username' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    update_user_timestamp(session['username'])
    
    data = request.get_json()
    lobby_code = lobby_code.upper()
    
    if lobby_code not in lobbies:
        return jsonify({'success': False, 'error': 'Lobby not found'}), 404
    
    lobby = lobbies[lobby_code]
    user_id = get_user_id()
    
    if lobby['host_id'] != user_id:
        return jsonify({'success': False, 'error': 'Only host can update'}), 403
    
    if 'min_range' in data:
        lobby['min_range'] = data['min_range']
    if 'max_range' in data:
        lobby['max_range'] = data['max_range']
    if 'max_players' in data:
        lobby['max_players'] = data['max_players']
    
    return jsonify({'success': True})

@zahlenraten.route('/api/leave-lobby/<lobby_code>', methods=['POST'])
def api_leave_lobby(lobby_code):
    track_request('leave_lobby')
    if 'username' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    update_user_timestamp(session['username'])
    
    lobby_code = lobby_code.upper()
    user_id = get_user_id()
    
    if lobby_code not in lobbies:
        return jsonify({'success': False, 'error': 'Lobby not found'}), 404
    
    lobby = lobbies[lobby_code]
    
    if lobby['host_id'] == user_id and lobby_code in lobby_members:
        members = lobby_members[lobby_code]
        other_members = [m for m in members if m['player_id'] != user_id]
        if other_members:
            new_host_id = other_members[0]['player_id']
            lobby['host_id'] = new_host_id
            for m in members:
                m['is_host'] = (m['player_id'] == new_host_id)
    
    if lobby_code in lobby_members:
        members_before = lobby_members[lobby_code]
        lobby_members[lobby_code] = [
            m for m in lobby_members[lobby_code] 
            if m['player_id'] != user_id
        ]
        members_after = lobby_members[lobby_code]
        
        if lobby_code in lobby_turn and lobby_turn[lobby_code] == user_id:
            if members_after:
                lobby_turn[lobby_code] = members_after[0]['player_id']
            else:
                if lobby_code in lobby_turn:
                    del lobby_turn[lobby_code]
    
    if lobby_code in lobby_spectators:
        lobby_spectators[lobby_code] = [
            p for p in lobby_spectators[lobby_code]
            if p != user_id
        ]
        
        if not lobby_spectators[lobby_code]:
            del lobby_spectators[lobby_code]
        
        if not lobby_members[lobby_code]:
            del lobbies[lobby_code]
            del lobby_members[lobby_code]
            if lobby_code in lobby_messages:
                del lobby_messages[lobby_code]
            if lobby_code in lobby_turn:
                del lobby_turn[lobby_code]
    elif not lobby_members[lobby_code]:
        del lobbies[lobby_code]
        del lobby_members[lobby_code]
        if lobby_code in lobby_messages:
            del lobby_messages[lobby_code]
        if lobby_code in lobby_turn:
            del lobby_turn[lobby_code]
    
    return jsonify({'success': True})
