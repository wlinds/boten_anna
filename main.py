import json, requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, Updater
from misc import *
import numpy as np


async def weather_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    print(f'{update.effective_user.first_name} requested /weather.')
    city = ' '.join(context.args)
    if not city:
        print(f'No city selected.')
        await update.message.reply_text("Please provide a city name.")
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
    print(f'{update.effective_user.first_name} requested /roll.')
    roll = np.random.randint(1,99)
    await update.message.reply_text(f'{update.effective_user.first_name} rolls {roll} (1-100)')
    print(f'Success. {roll=}.')


async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    print(f'{update.effective_user.first_name} requested /hello.')
    await update.message.reply_text(f'{welcome_message()}, {update.effective_user.first_name}')
    print(f'Success.')

async def googlar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = ' '.join(context.args)
    print(f'{update.effective_user.first_name} requested /google with {query=}.')
    if not query:
        print(f'No search query selected selected.')
        await update.message.reply_text("Please provide a search query.")
        return

    search_results = google_search(query, verbose=True)
    await update.message.reply_text(search_results)

def get_keys() -> tuple[str, str, str]:
    with open('keys.json') as f:
        keys = json.load(f)
    return keys["TOKEN"], keys["CHAT_ID"], keys["WEATHER"]
    # CHAT_ID is currently not used and can be removed. It might be used in the future however.

if __name__ == "__main__":
    TOKEN, CHAT_ID, WEATHER_KEY = get_keys()
    bot = ApplicationBuilder().token(TOKEN).build()

    bot.add_handler(CommandHandler("hello", hello))
    bot.add_handler(CommandHandler("weather", weather_command))
    bot.add_handler(CommandHandler("roll", roll_command))
    bot.add_handler(CommandHandler("google", googlar))
    
    print('Bot is running.')
    bot.run_polling()

