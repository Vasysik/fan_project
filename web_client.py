from flask import Flask, render_template, request, redirect, url_for
import socket
import json

app = Flask(__name__)

RPI_IP, RPI_PORT = input('IP:ПОРТ Распберри: ').split(':')
RPI_PORT = int(RPI_PORT)

def talk_to_rpi(payload={}):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        s.connect((RPI_IP, RPI_PORT))
        s.send(json.dumps(payload).encode('utf-8'))
        response = s.recv(4096).decode('utf-8')
        s.close()
        return json.loads(response)
    except:
        return None

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        fan_id = request.form.get('fan_id')
        action = request.form.get('action')
        
        payload = {'fan_id': fan_id}

        if action in ['change_mode', 'set_interval', 'set_target', 'toggle_manual', 'delete_fan']:
            payload['type'] = 'delete_fan' if action == 'delete_fan' else 'update'

            if action == 'change_mode':
                payload['mode'] = request.form.get('mode')
            elif action == 'set_interval':
                payload['temp_high'] = float(request.form.get('temp_high'))
                payload['temp_low'] = float(request.form.get('temp_low'))
            elif action == 'set_target':
                payload['target_temp'] = float(request.form.get('target_temp'))
            elif action == 'toggle_manual':
                state_str = request.form.get('state') 
                payload['manual_state'] = True if state_str == 'True' else False
            
            talk_to_rpi(payload)
            return redirect('/')

    data = talk_to_rpi()
    return render_template('index.html', data=data, ip=RPI_IP)

@app.route('/add', methods=['GET', 'POST'])
def add_fan():
    if request.method == 'POST':
        name = request.form.get('name')
        pin = request.form.get('pin')
        
        payload = {
            'type': 'add_fan',
            'name': name,
            'pin': pin
        }
        talk_to_rpi(payload)
        return redirect('/')
    
    return render_template('add.html')

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8000)
