import json, requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, Updater
from misc import *
import numpy as np


async def weather_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Get weather updates from any city/region"""
    
    print(f'{update.effective_user.first_name} requested /weather.')
    city = ' '.join(context.args)
    if not city:
        print(f'No city selected.')
        await update.message.reply_text("Please provide a city or region.")
        return

    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_KEY}"
    response = requests.get(url)
    data = response.json()

    if data["cod"] == 200:
        main_weather = data["weather"][0]["main"]
        description = data["weather"][0]["description"]
        temperature = data["main"]["temp"]
        temperature_celsius = temperature - 273.15
        humidity = data["main"]["humidity"]

        weather_info = f"Weather in {city}:\n" \
                       f"Main: {main_weather}\n" \
                       f"Description: {description}\n" \
                       f"Temperature: {temperature_celsius:.2f} °C\n" \
                       f"Humidity: {humidity}%"
        print(f'Success. \n{weather_info} posted.')

    else:
        print(f'Could not find city {city}.')
        weather_info = f"Failed to retrieve weather information for {city}."

    await update.message.reply_text(weather_info)


async def roll_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Roll a dice. Defaults to 1-100 but handles argument for any positive integer (dice sides)."""

    command_text = update.message.text.strip() # Extract the highest number from the command, if provided
    highest = 100  # Default highest number

    print(f'{update.effective_user.first_name} requested /roll, {command_text=}.')

    if len(command_text.split()) > 1:
        try:
            highest = int(command_text.split()[1])
            if highest <= 0:
                raise ValueError("Highest number must be a positive integer.")
        except ValueError:
            await update.message.reply_text(f"Can't roll die with {highest} sides. Try a positive integer.")
            return

    # Handle case if someone decides to roll one-sided dice
    if highest == 1:
        roll = 1
    else:
        roll = np.random.randint(1, highest)

    await update.message.reply_text(f'{update.effective_user.first_name} rolls {roll} (1-{highest})')
    print(f'Success. {roll=}.')

async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ Greets the user with welcome_message located in misc.py """

    print(f'{update.effective_user.first_name} requested /hello.')
    await update.message.reply_text(f'{welcome_message()}, {update.effective_user.first_name}')
    print(f'Success.')

async def googlar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Calls google_search() located in misc.py"""

    query = ' '.join(context.args)
    print(f'{update.effective_user.first_name} requested /google with {query=}.')
    if not query:
        print(f'No search query selected selected.')
        await update.message.reply_text("Please provide a search query.")
        return

    search_results = google_search(query, verbose=True)
    await update.message.reply_text(search_results)

def get_keys() -> tuple[str, str, str]:
    """Get keys from json.

    Create your own keys.json with this structure:

    {
    "TOKEN": "chatbot-token",
    "CHAT_ID": "your-chat-id",
    "WEATHER": "your-weather-api"
    }
    """
    
    with open('keys.json') as f:
        keys = json.load(f)
    return keys["TOKEN"], keys["CHAT_ID"], keys["WEATHER"]
    # CHAT_ID is currently not used and can be removed. It might be used in the future however.

if __name__ == "__main__":
    TOKEN, CHAT_ID, WEATHER_KEY = get_keys()
    bot = ApplicationBuilder().token(TOKEN).build()

    list_of_handlers = [
        ("hello", hello),
        ("weather", weather_command),
        ("roll", roll_command),
        ("google", googlar)
    ]

    for command, callback in list_of_handlers:
        bot.add_handler(CommandHandler(command, callback))


    print('Bot is running.')
    bot.run_polling()

