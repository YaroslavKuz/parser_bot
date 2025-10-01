import requests

TOKEN = '7049686288:AAE2_n25-fanmYcHGiF6oTe2Fsmt7VJ0wws' #токен
CHAT_ID = '-1002741092550'  # твій chat_id каналу

def send_telegram_message(text):
    url = f'https://api.telegram.org/bot{TOKEN}/sendMessage'
    data = {'chat_id': CHAT_ID, 'text': text}
    response = requests.post(url, data=data)
    print(response.json())

send_telegram_message("Привіт! Бот працює.")
