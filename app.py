from flask import Flask, request, jsonify, render_template
import requests
import json
from dotenv import load_dotenv
import os
import base64
import uuid

load_dotenv()

app = Flask(__name__, template_folder='templates')

# Конфигурация
AUTH_URL = 'https://ngw.devices.sberbank.ru:9443'
API_URL = 'https://gigachat.devices.sberbank.ru'
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')

def get_token():
    # Кодируем credentials в base64
    credentials = f"{CLIENT_ID}:{CLIENT_SECRET}"
    credentials_base64 = base64.b64encode(credentials.encode()).decode()
    
    # Генерируем уникальный идентификатор запроса
    rquid = str(uuid.uuid4())
    
    headers = {
        'Authorization': f'Basic {credentials_base64}',
        'RqUID': rquid,
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json'
    }
    
    print("\nОтправляем запрос авторизации:")
    print("URL:", f'{AUTH_URL}/api/v2/oauth')
    print("Headers:", headers)
    
    response = requests.post(
        f'{AUTH_URL}/api/v2/oauth',
        headers=headers,
        data='scope=GIGACHAT_API_PERS',
        verify=False
    )
    
    print("\nОтвет сервера авторизации:")
    print("Status:", response.status_code)
    print("Response:", response.text)
    
    if response.ok:
        return response.json()['access_token']
    else:
        response.raise_for_status()

def chat_completion(token, message):
    payload = {
        "model": "GigaChat",
        "messages": [
            {
                "role": "user",
                "content": message
            }
        ],
        "temperature": 0.7,
        "max_tokens": 1000,
        "stream": False
    }
    
    print("\nОтправляем запрос чата:")
    print("URL:", f'{API_URL}/api/v1/chat/completions')
    print("Payload:", json.dumps(payload, ensure_ascii=False, indent=2))
    
    response = requests.post(
        f'{API_URL}/api/v1/chat/completions',
        headers={
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {token}'
        },
        json=payload,
        verify=False
    )
    
    print("\nОтвет сервера чата:")
    print("Status:", response.status_code)
    print("Response:", response.text)
    
    if response.ok:
        return response.json()
    else:
        response.raise_for_status()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        user_message = request.json['message']
        print(f"\nПолучено сообщение: {user_message}")
        
        # Получаем токен
        token = get_token()
        print(f"\nПолучен токен: {token[:20]}...")
        
        # Отправляем запрос в чат
        response = chat_completion(token, user_message)
        
        return jsonify({
            'response': response['choices'][0]['message']['content']
        })
    except Exception as e:
        error_msg = str(e)
        print(f"\nОшибка: {error_msg}")
        if hasattr(e, 'response'):
            print("Response Status:", e.response.status_code)
            print("Response Headers:", dict(e.response.headers))
            print("Response Body:", e.response.text)
        return jsonify({'error': error_msg}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
