# flagbot
telegram bot using mysql database to store CTF flags for your command and give them only to admins

## setup:
```
pip install pyTelegramBotAPI
pip install asyncio
```
Your mysql db should contain events and flags tables.
Fill config.py file with credentials for mysql db, your bot token and telegram usernames of your team admins
