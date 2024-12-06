import asyncio
from telethon import TelegramClient, events
import json
import os
from datetime import datetime, timedelta

# Настройки бота
API_ID = '22273376'
API_HASH = '8bd050e7e9506f984ab5339ecf56d79e'
BOT_TOKEN = '7573725898:AAHm_7E8RP2XpNuUCRgawKbqLTgxZP2K7ec'

# Создаем клиент
client = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

class UserTracker:
    def __init__(self):
        self.tracked_users = {}
        self.load_data()

    def load_data(self):
        if os.path.exists('tracked_users.json'):
            with open('tracked_users.json', 'r') as f:
                self.tracked_users = json.load(f)

    def save_data(self):
        with open('tracked_users.json', 'w') as f:
            json.dump(self.tracked_users, f)

    async def track_user(self, user_id, event_time=None):
        if user_id not in self.tracked_users:
            self.tracked_users[user_id] = {'last_seen': None, 'activity_log': []}
        
        current_time = int(datetime.now().timestamp())
        
        if self.tracked_users[user_id]['last_seen'] is None:
            self.tracked_users[user_id]['last_seen'] = current_time
            self.tracked_users[user_id]['activity_log'].append(f"{datetime.fromtimestamp(current_time).strftime('%H:%M:%S')} был в сети")
        
        # Если прошло больше 10 секунд с последнего обновления
        elif current_time - self.tracked_users[user_id]['last_seen'] >= 10:
            last_seen_time = datetime.fromtimestamp(self.tracked_users[user_id]['last_seen']).strftime('%H:%M:%S')
            current_time_str = datetime.fromtimestamp(current_time).strftime('%H:%M:%S')
            self.tracked_users[user_id]['activity_log'].append(f"{last_seen_time} был в сети")
            self.tracked_users[user_id]['activity_log'].append(f"{current_time_str} вышел из сети")
            self.tracked_users[user_id]['last_seen'] = current_time

        # Ограничение количества записей в логе
        if len(self.tracked_users[user_id]['activity_log']) > 50:
            self.tracked_users[user_id]['activity_log'] = self.tracked_users[user_id]['activity_log'][:50]

        self.save_data()

tracker = UserTracker()

@client.on(events.NewMessage(pattern='/attack @username'))
async def attack(event):
    username = event.pattern_match.username
    user_id = await client.get_entity(username).id
    await tracker.track_user(user_id)
    await event.reply(f"Начало слежки за {username}")

@client.on(events.NewMessage(pattern='/report @username'))
async def report(event):
    username = event.pattern_match.username
    user_id = await client.get_entity(username).id
    
    if user_id in tracker.tracked_users:
        activity_log = tracker.tracked_users[user_id]['activity_log']
        
        if not activity_log:
            await event.reply("Пользователь не был активен")
        else:
            for entry in activity_log:
                await event.reply(entry)
    else:
        await event.reply("Пользователь не отслеживается")

@client.on(events.NewMessage(pattern='/stop @username'))
async def stop(event):
    username = event.pattern_match.username
    user_id = await client.get_entity(username).id
    
    if user_id in tracker.tracked_users:
        del tracker.tracked_users[user_id]
        tracker.save_data()
        await event.reply(f"Слежка за {username} остановлена")
    else:
        await event.reply("Пользователь не отслеживается")

@client.on(events.NewMessage(pattern='/help'))
async def help_command(event):
    commands = """
/attack @username - начать слежку
/report @username - получить информацию о активности
/stop @username - остановить слежку
/help - список команд
"""
    await event.reply(commands)

# Запуск бота
client.run_until_disconnected()
