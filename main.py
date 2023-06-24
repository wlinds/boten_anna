import json, requests, threading, schedule
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, Updater
from misc import *
import numpy as np
from pollen import pollen_gbg
import sr


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

    print(f'{update.effective_user.first_name} requested {command_text=}.')

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


async def start_timer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Starts a timer for the given number of seconds"""

    # TODO: Handle minutes and hours as well

    args = context.args
    if len(args) != 1:
        await update.message.reply_text("Invalid timer command. Usage: /timer <seconds>")
        return

    try:
        seconds = int(args[0])
    except ValueError:
        await update.message.reply_text("Invalid timer duration. Please provide a valid number of seconds.")
        return

    # Schedule the timer task
    threading.Timer(seconds, timer_done, args=[update, update.effective_user.first_name]).start()

    await update.message.reply_text(f"Timer started for {seconds} seconds.")
    print(f"Timer set by {update.effective_user.first_name} for {seconds} seconds.")

def timer_done(update: Update, user_name: str) -> None:
    """Sends a notification when a timer is done"""

    message = f"⏰ DING DONG! Timer set by {user_name} is done!"

    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": message})

    # Only ever use CHAT_ID here. Should be a better way to achieve this to avoid having to use CHAT_ID for this?
    # Or we keep it, I mean it is a very simple way to send messages.
    
    print(message)

async def add_to_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Adds item to list."""

    # Get the item from the user's message
    item = " ".join(context.args)

    # Check if the item is empty
    if not item:
        await update.message.reply_text("Please provide an item to add to the list.")
        return

    # Access or initialize the list in the context
    if "list" not in context.chat_data:
        context.chat_data["list"] = []

    # Add the item to the list
    context.chat_data["list"].append(item)

    # Reply with a confirmation message
    await update.message.reply_text(f"Item '{item}' added to the list.")


async def remove_from_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Removes item from list."""

    # Get the item to be removed from the user's message
    item = " ".join(context.args)

    # Check if the item is empty
    if not item:
        await update.message.reply_text("Please provide an item to remove from the list.")
        return

    # Access the list in the context
    if "list" not in context.chat_data or not context.chat_data["list"]:
        await update.message.reply_text("The list is empty.")
        return

    # Remove the item from the list if it exists
    if item in context.chat_data["list"]:
        context.chat_data["list"].remove(item)
        await update.message.reply_text(f"Item '{item}' removed from the list.")
    else:
        await update.message.reply_text(f"Item '{item}' not found in the list.")


async def clear_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Clears the entire list."""

    # Access the list in the context
    if "list" not in context.chat_data or not context.chat_data["list"]:
        await update.message.reply_text("The list is already empty.")
        return

    # Clear the list
    context.chat_data["list"] = []
    await update.message.reply_text("The list has been cleared.")

  
async def display_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays the items in the list."""

    # Access the list in the context
    if "list" not in context.chat_data or not context.chat_data["list"]:
        await update.message.reply_text("The list is empty.")
        return

    # Get the items from the list
    items = context.chat_data["list"]

    # Format the items as a string
    items_str = "\n".join(items)

    # Send the formatted list as a message
    await update.message.reply_text(f"The list contains:\n{items_str}")


async def pollenrapport(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text, link = pollen_gbg()
    message = f"{text}\n\n{link}"

    await update.message.reply_text(message)


def get_keys() -> tuple[str, str, str]:
    """Get keys from json.

    Create your own keys.json with this structure:

    {
    "TOKEN": "chatbot-token",
    "CHAT_ID": "your-chat-id",
    "WEATHER": "your-weather-api"
    }
    """
    
    with open('keys-groupchat.json') as f:
        keys = json.load(f)
    return keys["TOKEN"], keys["CHAT_ID"], keys["WEATHER"]

if __name__ == "__main__":
    TOKEN, CHAT_ID, WEATHER_KEY = get_keys()
    bot = ApplicationBuilder().token(TOKEN).build()

    handlers = [
        ("hello", hello),
        ("weather", weather_command),
        ("roll", roll_command),
        ("google", googlar),
        ("timer", start_timer),
        ("add", add_to_list),
        ("remove", remove_from_list),
        ("clear", clear_list),
        ("display", display_list),
        ("pollen", pollenrapport)
    ]

    for command, callback in handlers:
        bot.add_handler(CommandHandler(command, callback))

    print('Bot is running.')
    bot.run_polling()