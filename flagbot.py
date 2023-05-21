import mysql.connector
import datetime
import telebot
from telebot import asyncio_filters
from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_storage import StateMemoryStorage
from telebot.asyncio_handler_backends import State, StatesGroup
import asyncio
import config

# Connect to MariaDB
db = mysql.connector.connect(
  host = config.HOST,
  user = config.USER,
  password = config.PASSWORD,
  database = config.DATABASE
)

# Create cursor to execute SQL queries
cursor = db.cursor()

# Create list of admin usernames
admin_list = config.ADMINS

# Initialize bot with bot token
bot = AsyncTeleBot(config.TOKEN, state_storage=StateMemoryStorage())

class MyStates(StatesGroup):
    task = State()
    flag = State() # statesgroup should contain states
    event = State()
    template = State()

def log(text, filename='log.txt'):
    with open(filename, 'a') as logfile:
        logfile.write(str(text)+str(gettime())+'\n')

def cancelbutton():
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.add(telebot.types.InlineKeyboardButton(text="Отмена", callback_data="/cancel"))
    return keyboard

@bot.message_handler(state=MyStates.event)
async def event_get(message):
    """
    State 1. Will process when user's state is MyStates.task.
    """
    keyboard = cancelbutton()
    await bot.send_message(message.chat.id, f'Введите образец флага, наример SomeCTF{{}}:', reply_markup=keyboard)
    await bot.set_state(message.from_user.id, MyStates.template, message.chat.id)
    async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['event'] = message.text

@bot.message_handler(state=MyStates.template)
async def template_get(message):
    template = message.text
    async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        event = data['event']
    setzero_query = "UPDATE events SET iscurrent=0"
    insert_query = "INSERT INTO events(event, template, iscurrent) VALUES (%s, %s, %s)"
    insert_values = (event, template, 1)
    cursor.execute(setzero_query)
    cursor.execute(insert_query, insert_values)
    db.commit()
    # Send a confirmation to the user
    username = message.from_user.username
    async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        await bot.send_message(message.chat.id, "Новый ивент создан и назначен текущим.")
    await bot.delete_state(message.from_user.id, message.chat.id)
    log('template_get:'+' '+str(username)+' '+str(event)+' '+str(template))
    await start(message)

@bot.message_handler(state=MyStates.task)
async def task_get(message):
    keyboard = cancelbutton()
    await bot.send_message(message.chat.id, f'Введите флаг:', reply_markup=keyboard)
    await bot.set_state(message.from_user.id, MyStates.flag, message.chat.id)
    async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['task'] = message.text

@bot.message_handler(state=MyStates.flag)
async def flag_get(message):
    """
    State 3. Will process when user's state is MyStates.age.
    """
    flag = message.text
    async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        task = data['task']
    try:
        cursor.execute("SELECT event FROM events WHERE iscurrent = 1")
        current_event = cursor.fetchone()[0]
    except:
        await bot.send_message(message.chat.id, "Ошибка: Отсутствует текущий ивент. Это означает, что в данный момент в команде не проходит CTF.\nЕсли это не так, обратитесь к администратору c просьбой добавить новый ивент или сделать текущим один из существующих.")
        await bot.delete_state(message.from_user.id, message.chat.id)
        await start(message)
        return 0
    username = message.from_user.username
    submit_time = gettime()
    insert_query = "INSERT INTO flags(username, event, task, flag, submit_time) VALUES (%s, %s, %s, %s, %s)"
    insert_values = (username, current_event, task, flag, submit_time)
    cursor.execute(insert_query, insert_values)
    db.commit()
    # Send a confirmation to the user
    async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        await bot.send_message(message.chat.id, "Красавчик! Флаг принят!")
    await bot.delete_state(message.from_user.id, message.chat.id)
    log('flag_get:'+' '+str(username)+' '+str(flag)+' '+str(task))
    await start(message)

def gettime():
    now = datetime.datetime.now()
    formatted_date = now.strftime('%Y-%m-%d %H:%M:%S')
    return formatted_date

def startkeyboard(username):
    keyboard = telebot.types.InlineKeyboardMarkup()
    if username in admin_list:
        keyboard.add(telebot.types.InlineKeyboardButton(text="Добавить флаг", callback_data="/addflag"))
        keyboard.add(telebot.types.InlineKeyboardButton(text="Текущий ивент", callback_data="/showcurrent"))
        keyboard.add(telebot.types.InlineKeyboardButton(text="Ивенты", callback_data="/events"))
        keyboard.add(telebot.types.InlineKeyboardButton(text="Добавить текущий ивент", callback_data="/addevent"))
        keyboard.add(telebot.types.InlineKeyboardButton(text="Сделать ивент текущим", callback_data="/setcurrent"))
        keyboard.add(telebot.types.InlineKeyboardButton(text="Удалить ивент", callback_data="/deleteevent"))
        keyboard.add(telebot.types.InlineKeyboardButton(text="Мои флаги", callback_data="/myflags"))
        keyboard.add(telebot.types.InlineKeyboardButton(text="Все флаги", callback_data="/flags"))
        keyboard.add(telebot.types.InlineKeyboardButton(text="Текущие флаги", callback_data="/currentflags"))
        keyboard.add(telebot.types.InlineKeyboardButton(text="Удалить невалидный флаг", callback_data="/deleteflag"))
    else:
        keyboard.add(telebot.types.InlineKeyboardButton(text="Добавить флаг", callback_data="/addflag"))
        keyboard.add(telebot.types.InlineKeyboardButton(text="Текущий ивент", callback_data="/showcurrent"))
        keyboard.add(telebot.types.InlineKeyboardButton(text="Мои флаги", callback_data="/myflags"))
        keyboard.add(telebot.types.InlineKeyboardButton(text="Удалить невалидный флаг", callback_data="/deleteflag"))
    return keyboard

async def start(message):
    username = message.from_user.username
    keyboard = startkeyboard(username)
    await bot.send_message(message.chat.id, "Доступные команды:", reply_markup=keyboard)
        
async def startcallback(call):
    username = call.from_user.username
    keyboard = startkeyboard(username)
    await bot.send_message(call.message.chat.id, "Доступные команды:", reply_markup=keyboard)

def isadmin(call):
    username = call.from_user.username
    if username in admin_list:
        return True
    else:
        return False

async def addflag(call):
    await bot.set_state(call.message.chat.id, MyStates.task, call.message.chat.id)
    keyboard = cancelbutton()
    await bot.send_message(call.message.chat.id, 'Введите название таска:', reply_markup=keyboard)
    # Select the current event from the events table
    

async def showevents(call):
    if isadmin(call) == True:
        username = call.from_user.username
        cursor = db.cursor()
        cursor.execute("SELECT event FROM events")
        rows = cursor.fetchall()
        response_message = 'Events:\n'
        for row in rows:
            response_message += str(row[0]+'\n')
        log(str(username)+' '+str(response_message))
        await bot.send_message(call.message.chat.id, response_message)
    else:
        await bot.send_message(call.message.chat.id, 'Недостаточно прав')
    await startcallback(call)

async def addevent(call):
    await bot.set_state(call.message.chat.id, MyStates.event, call.message.chat.id)
    keyboard = cancelbutton()
    await bot.send_message(call.message.chat.id, 'ВНИМАНИЕ: Новый ивент сразу будет сделан текущим. Если вы не уверены, нажмите \'Отмена\'.\nВведите название ивента:', reply_markup=keyboard)
    # Select the current event from the events table

@bot.message_handler(state=MyStates.event)
async def event_get(message):
    """
    State 1. Will process when user's state is MyStates.name.
    """
    async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        await bot.send_message(message.chat.id, message.text)
    
async def showcurrentflags(call):
    username = call.from_user.username
    if username in admin_list:
        cursor = db.cursor()
        cursor.execute("SELECT event FROM events WHERE iscurrent = 1")
        current_event = cursor.fetchone()[0]
        select_query = "SELECT event, flag, task, username, submit_time FROM flags WHERE event = %s"
        select_values = (current_event,)
        cursor.execute(select_query, select_values)
        flags = cursor.fetchall()
        cursor.close()
        response_message = ''
        for flag in flags:
            string = ''
            for i in range(0,len(flag)):
                string += str(flag[i])+' # '
            response_message += string+'\n'
            response_message += '################\n'
        await bot.send_message(call.message.chat.id, response_message)
        log('showcurrentflags:'+' '+str(username)+' '+str(flags))
    else:
        await bot.send_message(call.message.chat.id, "Недостаточно прав.")
    await startcallback(call)

async def showmyflags(call):
    username = call.from_user.username
    cursor = db.cursor()
    select_query = "SELECT DISTINCT event FROM flags WHERE username = %s"
    select_values = (username,)
    cursor.execute(select_query, select_values)
    events = cursor.fetchall()
    cursor.close()
    keyboard = telebot.types.InlineKeyboardMarkup()
    log('showmyflags:'+' '+str(username)+' '+str(events))
    # Create a list of buttons for each event
    for event in events:
        keyboard.add(telebot.types.InlineKeyboardButton(text=str(event[0]), callback_data=str(event[0])))
    keyboard.add(telebot.types.InlineKeyboardButton(text="Отмена", callback_data="/cancel"))
    # Create a custom keyboard with the event buttons and send
    await bot.send_message(call.message.chat.id, 'Выберите ивент:', reply_markup=keyboard)

    

async def showallflags(call):
    username = call.from_user.username
    if username in admin_list:
        cursor = db.cursor()
        select_query = "SELECT DISTINCT event FROM flags"
        cursor.execute(select_query)
        events = cursor.fetchall()
        cursor.close()
        keyboard = telebot.types.InlineKeyboardMarkup()
        log('showallflags:'+' '+str(username)+' '+str(events))
        # Create a list of buttons for each event
        for event in events:
            keyboard.add(telebot.types.InlineKeyboardButton(text=str(event[0]), callback_data=str('showallflags'+'$##$'+event[0])))
        keyboard.add(telebot.types.InlineKeyboardButton(text="Отмена", callback_data="/cancel"))
        # Create a custom keyboard with the event buttons and send
        await bot.send_message(call.message.chat.id, 'Выберите ивент:', reply_markup=keyboard)
    else:
        await bot.send_message(call.message.chat.id, "Недостаточно прав.")
        await startcallback(call)

async def deleteevent(call):
    username = call.from_user.username
    if username in admin_list:
        cursor = db.cursor()
        select_query = "SELECT DISTINCT event FROM events"
        cursor.execute(select_query)
        events = cursor.fetchall()
        cursor.close()
        keyboard = telebot.types.InlineKeyboardMarkup()
        log('deleteevent:'+' '+str(username)+' '+str(events))
        # Create a list of buttons for each event
        for event in events:
            keyboard.add(telebot.types.InlineKeyboardButton(text=str(event[0]), callback_data=str('deleteevent'+'$##$'+event[0])))
        keyboard.add(telebot.types.InlineKeyboardButton(text="Отмена", callback_data="/cancel"))
        # Create a custom keyboard with the event buttons and send
        await bot.send_message(call.message.chat.id, 'Выберите ивент:', reply_markup=keyboard)
    else:
        await bot.send_message(call.message.chat.id, "Недостаточно прав.")
        await startcallback(call)

async def deleteflag(call):
    username = call.from_user.username
    if username in admin_list:
        cursor = db.cursor()
        select_query = "SELECT flag FROM flags"
        cursor.execute(select_query)
        flags = cursor.fetchall()
        print(flags)
        cursor.close()
        keyboard = telebot.types.InlineKeyboardMarkup()
        log('deleteflag:'+' '+str(username)+' '+str(flags))
        # Create a list of buttons for each event
        for flag in flags:
            keyboard.add(telebot.types.InlineKeyboardButton(text=str(flag[0]), callback_data=str('deleteflag'+'$##$'+flag[0])))
        keyboard.add(telebot.types.InlineKeyboardButton(text="Отмена", callback_data="/cancel"))
        # Create a custom keyboard with the event buttons and send
        await bot.send_message(call.message.chat.id, 'Выберите флаг:', reply_markup=keyboard)
    else:
        cursor = db.cursor()
        select_query = "SELECT flag FROM flags WHERE username = %s"
        select_values = (username,)
        cursor.execute(select_query, select_values)
        flags = cursor.fetchall()
        print(flags)
        cursor.close()
        keyboard = telebot.types.InlineKeyboardMarkup()
        log('deleteflag:'+' '+str(username)+' '+str(flags))
        # Create a list of buttons for each event
        for flag in flags:
            keyboard.add(telebot.types.InlineKeyboardButton(text=str(flag[0]), callback_data=str('deleteflag'+'$##$'+flag[0])))
        keyboard.add(telebot.types.InlineKeyboardButton(text="Отмена", callback_data="/cancel"))
        # Create a custom keyboard with the event buttons and send
        await bot.send_message(call.message.chat.id, 'Выберите флаг:', reply_markup=keyboard)

async def setcurrent(call):
    username = call.from_user.username
    if username in admin_list:
        cursor = db.cursor()
        select_query = "SELECT DISTINCT event FROM events"
        cursor.execute(select_query)
        events = cursor.fetchall()
        cursor.close()
        keyboard = telebot.types.InlineKeyboardMarkup()
        log('setcurrent:'+' '+str(username)+' '+str(events))
        # Create a list of buttons for each event
        for event in events:
            keyboard.add(telebot.types.InlineKeyboardButton(text=str(event[0]), callback_data=str('setcurrent'+'$##$'+event[0])))
        keyboard.add(telebot.types.InlineKeyboardButton(text="Отмена", callback_data="/cancel"))
        # Create a custom keyboard with the event buttons and send
        await bot.send_message(call.message.chat.id, 'Выберите ивент:', reply_markup=keyboard)
    else:
        await bot.send_message(call.message.chat.id, "Недостаточно прав.")
        await startcallback(call)

@bot.message_handler(commands=['start'])
async def handle_start_command(message):
    await start(message)

@bot.message_handler(state="*", commands='cancel')
async def any_state(message):
    """
    Cancel state
    """
    await bot.send_message(message.chat.id, "Ладно...")
    await bot.delete_state(message.from_user.id, message.chat.id)

# Define a function for handling callbacks from button presses
@bot.callback_query_handler(func=lambda call: True)
async def handle_callback_query(call):
    username = call.from_user.username
    cursor = db.cursor()
    select_query = "SELECT DISTINCT event FROM flags WHERE username = %s"
    select_values = (username,)
    cursor.execute(select_query, select_values)
    events = cursor.fetchall()
    cursor.close()
    eventlist = []
    for event in events:
        eventlist.append(event[0])
    if call.data == "/start":
        # Handle "/start" command separately
        await startcallback(call)
        return 0
    elif call.data == "/addflag":
        # Handle "/start" command separately
        await addflag(call)
        return 0
    elif call.data == "/events":
        # Handle "/start" command separately
        await showevents(call)
        return 0
    elif call.data == "/addevent":
        # Handle "/start" command separately
        await addevent(call)
        return 0
    elif call.data == "/setcurrent":
        # Handle "/start" command separately
        await setcurrent(call)
        return 0
    elif call.data == "/myflags":
        # Handle "/start" command separately
        await showmyflags(call)
        return 0
    elif call.data == "/currentflags":
        # Handle "/start" command separately
        await showcurrentflags(call)
        return 0
    elif call.data == "/flags":
        # Handle "/start" command separately
        await showallflags(call)
        return 0
    elif call.data == "/deleteevent":
        # Handle "/start" command separately
        await deleteevent(call)
        return 0
    elif call.data == "/deleteflag":
        # Handle "/start" command separately
        await deleteflag(call)
        return 0
    elif call.data == "/cancel":
        # Handle "/start" command separately
        await bot.send_message(call.message.chat.id, "Отмена...")
        await bot.delete_state(call.message.chat.id, call.message.chat.id)
        await startcallback(call)
        return 0
    elif call.data == "/showcurrent":
        cursor = db.cursor()
        get_event_query = "SELECT event FROM events WHERE iscurrent=1"
        cursor.execute(get_event_query)
        event = cursor.fetchone()[0]
        print(event)
        cursor.close()
        if len(event) > 1:
            await bot.send_message(call.message.chat.id, str('Текущий ивент: '+event))
            await startcallback(call)
            return 0
        else:
            await bot.send_message(call.message.chat.id, "Ошибка: Отсутствует текущий ивент. Это означает, что в данный момент в команде не проходит CTF.\nЕсли это не так, обратитесь к администратору c просьбой добавить новый ивент или сделать текущим один из существующих.")
            await startcallback(call)
            return 0
        
    elif call.data in eventlist:
        cursor = db.cursor()
        select_query = "SELECT username, task, flag FROM flags WHERE event = %s AND username = %s"
        select_values = (call.data,username,)
        cursor.execute(select_query, select_values)
        flags = cursor.fetchall()
        log('eventcallback:'+' '+str(username)+' '+str(flags))
        response_message = ''
        for flag in flags:
            string = ''
            for i in range(0,len(flag)):
                string += str(flag[i])+' '
            response_message += string+'\n'
        await bot.send_message(call.message.chat.id, response_message)
        cursor.close()
        await startcallback(call)
    elif call.data.split('$##$')[0] == 'showallflags':
        cursor = db.cursor()
        select_query = "SELECT flag, task, username, submit_time FROM flags WHERE event = %s"
        select_values = (call.data.split('$##$')[1],)
        cursor.execute(select_query, select_values)
        flags = cursor.fetchall()
        cursor.close()
        response_message = ''
        for flag in flags:
            string = ''
            for i in range(0,len(flag)):
                string += str(flag[i])+' # '
            response_message += string+'\n'
            response_message += '################\n'
        log('showcurrentflags:'+' '+str(username)+' '+str(flags))
        await bot.send_message(call.message.chat.id, response_message)
        await startcallback(call)
    elif call.data.split('$##$')[0] == 'deleteevent':
        cursor = db.cursor()
        delete_event_query = "DELETE FROM events WHERE event = %s"
        delete_event_values = (call.data.split('$##$')[1],)
        cursor.execute(delete_event_query, delete_event_values)
        # delete_flags_query = "DELETE FROM flags WHERE event = %s"
        # delete_flags_values = (call.data.split('$##$')[1],)
        # cursor.execute(delete_flags_query, delete_flags_values)
        db.commit()
        cursor.close()
        response_message = str(call.data.split('$##$')[1]+': ивент успешно удалён')
        await bot.send_message(call.message.chat.id, response_message)
        await startcallback(call)
    elif call.data.split('$##$')[0] == 'deleteflag':
        for text in call.data.split('$##$'):
            print(text)
        cursor = db.cursor()
        delete_flags_query = "DELETE FROM flags WHERE flag = %s"
        delete_flags_values = (call.data.split('$##$')[1],)
        cursor.execute(delete_flags_query, delete_flags_values)
        db.commit()
        cursor.close()
        response_message = str(call.data.split('$##$')[1]+': флаг успешно удалён')
        await bot.send_message(call.message.chat.id, response_message)
        await startcallback(call)
    elif call.data.split('$##$')[0] == 'setcurrent':
        cursor = db.cursor()
        setzero_query = "UPDATE events SET iscurrent=0"
        set_event_query = "UPDATE events SET iscurrent=1 WHERE event = %s"
        set_event_values = (call.data.split('$##$')[1],)
        cursor.execute(setzero_query)
        cursor.execute(set_event_query, set_event_values)
        db.commit()
        cursor.close()
        response_message = str(call.data.split('$##$')[1]+': ивент успешно сделан текущим')
        await bot.send_message(call.message.chat.id, response_message)
        await startcallback(call)

bot.add_custom_filter(asyncio_filters.StateFilter(bot))

asyncio.run(bot.polling())