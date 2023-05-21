# flagbot
telegram bot using mysql database to store CTF flags for your team
bot rerutns requested flags only to admins

## Setup:
```
pip install pyTelegramBotAPI
pip install asyncio
```
Your mysql db should contain events and flags tables.
Fill config.py file with credentials for mysql db, your bot token and telegram usernames of your team admins

## usage:
start bot with /start command, and click buttons ))
### User can:
- add flag
- see current event
- see his own flags
- delete invalid flag
### Admin user can do everything what usual user can, and:
- see all events
- add current event
- delete event
- make event current
- see all flags
- see flags from current event

If you have suggestions, questions, or got errors, feel free to write me in telegram: [@peka_boyarin](t.me/peka_boyarin)
