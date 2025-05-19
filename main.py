import logging
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from utils.env_utils import get_env_vars
from handlers.command_handlers import register_command_handlers
from handlers.message_handlers import handle_message
from handlers.scheduled_tasks import schedule_tasks

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def main():
    TOKEN, CHAT_ID, WEATHER_KEY, OPENAI_KEY, GOOGLE_KEY, _ = get_env_vars()
    bot = ApplicationBuilder().token(TOKEN).build()
    register_command_handlers(bot)
    bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    schedule_tasks(bot)

    print('[🤖] Bot is running.')
    bot.run_polling()

if __name__ == "__main__":
    main()