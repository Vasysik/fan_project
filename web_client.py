from flask import Flask, render_template, request, redirect, url_for
import socket
import json
import argparse

app = Flask(__name__)

def parse_arguments():
    """
    Парсит аргументы командной строки.

    :return: Пространство имён с аргументами.
    :rtype: argparse.Namespace
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--ip', default='0.0.0.0')
    parser.add_argument('--port', default=5000)
    return parser.parse_args()

def talk_to_rpi(payload={}):
    """
    Отправляет JSON-запрос серверу управления вентиляторами через сокет.
    
    :param payload: Словарь с данными для отправки. По умолчанию пустой.
    :type payload: dict
    :return: Ответ от сервера в виде словаря или None при ошибке.
    :rtype: dict or None
    """
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
    """
    Обработчик главной страницы веб-интерфейса.
    
    В GET-запросе: Запрашивает данные у демона и рендерит страницу.
    В POST-запросе: Обрабатывает действия пользователя (смена режима, удаление и т.д.).

    :return: HTML-страница или перенаправление.
    """
    if request.method == 'POST':
        fan_id = request.form.get('fan_id')
        action = request.form.get('action')
        payload = {'fan_id': fan_id}

        if action == 'delete_fan':
            payload['type'] = 'delete_fan'
        else:
            payload['type'] = 'update'

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
    """
    Обработчик страницы добавления нового вентилятора.

    :return: HTML-страница добавления или перенаправление на главную после успеха.
    """
    data = talk_to_rpi()
    
    if request.method == 'POST':
        name = request.form.get('name')
        pin = request.form.get('pin')
        sensor_id = request.form.get('sensor_id')
        
        payload = {
            'type': 'add_fan',
            'name': name,
            'pin': pin,
            'sensor_id': sensor_id
        }
        talk_to_rpi(payload)
        return redirect('/')
    
    return render_template('add.html', data=data)

if __name__ == '__main__':
    args = parse_arguments()
    RPI_IP = args.ip
    RPI_PORT = int(args.port)
    app.run(debug=False, host='0.0.0.0', port=8000)
