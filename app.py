# 1. 반드시 최상단(다른 모든 import보다 위)에 위치해야 합니다.
import eventlet
eventlet.monkey_patch()

import os
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
# 2. 보안 및 컨텍스트 설정을 위해 아래 옵션을 추가합니다.
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# ... 나머지 게임 로직 (players 등)은 그대로 유지 ...

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    # 3. Render 환경에서는 socketio.run을 직접 호출합니다.
    socketio.run(app, host='0.0.0.0', port=port)

from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# 접속자 정보 저장 (예: { sid: {'name': '철수', 'pick': '가위'} })
players = {}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('join')
def handle_join(data):
    # 사용자가 입력한 이름을 ID와 연결하여 저장
    players[request.sid] = {'name': data['name'], 'pick': None}
    print(f"{data['name']}님이 입장하셨습니다.")

@socketio.on('choice')
def handle_choice(data):
    if request.sid in players:
        players[request.sid]['pick'] = data['pick']
    
    # 두 명의 선택이 모두 완료되었는지 확인
    ready_players = [sid for sid, info in players.items() if info['pick'] is not None]
    
    if len(ready_players) == 2:
        p1_sid, p2_sid = ready_players
        p1 = players[p1_sid]
        p2 = players[p2_sid]
        
        # 승패 판정
        if p1['pick'] == p2['pick']:
            res = "무승부입니다!"
        elif (p1['pick'] == "가위" and p2['pick'] == "보") or \
             (p1['pick'] == "바위" and p2['pick'] == "가위") or \
             (p1['pick'] == "보" and p2['pick'] == "바위"):
            res = f"{p1['name']}님 승리!"
        else:
            res = f"{p2['name']}님 승리!"
            
        emit('game_result', {
            'winner': res,
            'p1_name': p1['name'], 'p1_pick': p1['pick'],
            'p2_name': p2['name'], 'p2_pick': p2['pick']
        }, broadcast=True)
        
        # 다음 판을 위해 선택 초기화
        for sid in players:
            players[sid]['pick'] = None
    else:
        emit('update', {'msg': "상대방의 선택을 기다리고 있습니다..."}, broadcast=True)

if __name__ == '__main__':
    # 포트를 지정하지 않거나 Render가 주는 환경변수를 사용해야 합니다.
    import os
    port = int(os.environ.get('PORT', 10000))
    socketio.run(app, host='0.0.0.0', port=port)
# 기존 choice 핸들러 아래에 추가하세요
@socketio.on('message')
def handle_message(data):
    # 전송한 사람의 닉네임을 찾고 메시지와 함께 브로드캐스트
    name = players.get(request.sid, {}).get('name', '익명')
    emit('new_message', {'name': name, 'msg': data['msg']}, broadcast=True)

