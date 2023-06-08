import json
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from misc import *
import numpy as np

# CHAT_ID is currently not used and can be removed. It might be used in the future however.
with open('keys.json') as f:
    keys = json.load(f)
TOKEN, CHAT_ID, WEATHER_KEY = keys["TOKEN"], keys["CHAT_ID"], keys["WEATHER"]


async def get_weather(city: str) -> str:
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
    else:
        weather_info = f"Failed to retrieve weather information for {city}."

    return weather_info


async def weather_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Get the text after the command as the city
    city = ' '.join(context.args)
    if not city:
        await update.message.reply_text("Please provide a city name.")
        return
    
    weather_info = await get_weather(city)
    await update.message.reply_text(weather_info)


async def roll_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f'{update.effective_user.first_name} rolls {np.random.randint(1,99)} (1-100)')


async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f'{welcome_message()}, {update.effective_user.first_name}')



if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("hello", hello))
    app.add_handler(CommandHandler("weather", weather_command))
    app.add_handler(CommandHandler("roll", roll_command))
    
    app.run_polling()

    print('Bot started.')
