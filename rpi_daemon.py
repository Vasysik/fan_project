import socket
import json
import threading
import time
import os
try: import RPi.GPIO as GPIO
except: print("Библиотека RPi.GPIO не найдена")

HOST = '0.0.0.0'
PORT = 5000
CONFIG_FILE = 'config.json'

system_data = {
    "cpu_temp": 0.0,
    "fans": [] 
}

def load_config():
    try:
        with open(CONFIG_FILE, 'r') as f:
            data = json.load(f)
            system_data['fans'] = data['fans']
    except FileNotFoundError:
        system_data['fans'] = []

def save_config():
    with open(CONFIG_FILE, 'w') as f:
        json.dump({"fans": system_data['fans']}, f, indent=2, ensure_ascii=False)

def setup_gpio():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    for fan in system_data['fans']:
        GPIO.setup(int(fan['pin']), GPIO.OUT)
        GPIO.output(int(fan['pin']), fan['state'])

def get_cpu_temp():
    try:
        with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
            return float(f.read()) / 1000.0
    except:
        return 45.0

def update_fan_logic(fan, temp):
    mode = fan['mode']
    p = fan['params']
    
    new_state = fan['state']

    if mode == 'interval':
        if temp >= p['temp_high']:
            new_state = True
        elif temp <= p['temp_low']:
            new_state = False
            
    elif mode == 'target':
        if temp > p['target_temp']:
            new_state = True
        else:
            new_state = False
            
    elif mode == 'manual':
        new_state = p['manual_state']
    
    return new_state

def control_loop():
    while True:
        temp = get_cpu_temp()
        system_data['cpu_temp'] = temp
        
        state_changed = False

        for fan in system_data['fans']:
            target_state = update_fan_logic(fan, temp)
            if fan['state'] != target_state:
                fan['state'] = target_state
                GPIO.output(int(fan['pin']), target_state)
                state_changed = True
        
        if state_changed:
            save_config()
        time.sleep(0.2)

def socket_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(5)

    print(f"Сервер запущен: {HOST}:{PORT} ({os.popen('hostname -I').read().split()[0]}:{PORT})")

    while True:
        try:
            client, addr = server.accept()
            req = client.recv(4096).decode('utf-8')
            
            if req:
                cmd = json.loads(req)
                need_save = False

                if cmd.get('type') == 'update':
                    target_id = cmd['fan_id']
                    for fan in system_data['fans']:
                        if fan['id'] == target_id:
                            if 'mode' in cmd: fan['mode'] = cmd['mode']
                            if 'name' in cmd: fan['name'] = cmd['name']
                            for key in ['temp_high', 'temp_low', 'target_temp', 'manual_state']:
                                if key in cmd:
                                    fan['params'][key] = cmd[key]
                            
                            temp = system_data['cpu_temp']
                            new_state = update_fan_logic(fan, temp)
                            fan['state'] = new_state
                            GPIO.output(int(fan['pin']), new_state)
                            
                            need_save = True

                elif cmd.get('type') == 'add_fan':
                    new_fan = {
                        "id": f"fan_{int(time.time())}",
                        "name": cmd['name'],
                        "pin": int(cmd['pin']),
                        "mode": "manual",
                        "state": False,
                        "params": {"temp_high": 60, "temp_low": 45, "target_temp": 50, "manual_state": False}
                    }
                    system_data['fans'].append(new_fan)
                    GPIO.setup(new_fan['pin'], GPIO.OUT)
                    need_save = True

                elif cmd.get('type') == 'delete_fan':
                    for fan in system_data['fans']:
                        if fan['id'] == cmd['fan_id']:
                            GPIO.output(int(fan['pin']), False)
                            break
                    system_data['fans'] = [f for f in system_data['fans'] if f['id'] != cmd['fan_id']]
                    need_save = True
                
                if need_save:
                    save_config()
            
            resp = json.dumps(system_data)
            client.send(resp.encode('utf-8'))
            client.close()
        except Exception as e:
            print(f"Socket error: {e}")

if __name__ == '__main__':
    try:
        load_config()
        setup_gpio()
        t = threading.Thread(target=control_loop)
        t.daemon = True
        t.start()
        socket_server()
    except KeyboardInterrupt:
        GPIO.cleanup()
