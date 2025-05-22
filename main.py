import logging, os
from utils.env_utils import validate_required_vars
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from utils.env_utils import get_env_vars
from handlers.command_handlers import register_command_handlers
from handlers.message_handlers import handle_message
from handlers.scheduled_tasks import schedule_tasks
from services.scheduler_service import scheduler_service

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def main():
    try:
        validate_required_vars()
        print("✅ All required environment variables are set")
    except EnvironmentError as e:
        print(f"❌ {e}")
        return

    TOKEN = os.getenv('TELEGRAM_TOKEN')
    bot = ApplicationBuilder().token(TOKEN).build()
    register_command_handlers(bot)
    bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    schedule_tasks(bot)
    scheduler_service.schedule_jobs(bot.job_queue)
    print('[🤖] Bot is running.')
    bot.run_polling()

if __name__ == "__main__":
    main()