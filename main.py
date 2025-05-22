import logging, os
from utils.env_utils import validate_required_vars
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from handlers.command_handlers import register_command_handlers
from handlers.message_handlers import handle_message
from handlers.scheduled_tasks import schedule_tasks
from services.scheduler_service import scheduler_service

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def main():
    print("🔍 DEBUG: Available environment variables:")
    for key in sorted(os.environ.keys()):
        if any(x in key.upper() for x in ['TELEGRAM', 'TOKEN', 'CHAT', 'API', 'WEATHER', 'OPENAI']):
            value = os.getenv(key)
            print(f"  {key}: {'✅ SET' if value else '❌ NOT SET'}")
    
    required_vars = ['TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID', 'OPENWEATHERMAP_API_KEY']
    print("\n🔍 Checking required variables:")
    for var in required_vars:
        value = os.getenv(var)
        print(f"  {var}: {'✅ SET' if value else '❌ NOT SET'}")
    
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        print(f"\n❌ Missing: {missing}")
        print("\n🔍 ALL environment variables:")
        for key, value in sorted(os.environ.items()):
            print(f"  {key}: {value[:20]}..." if len(value) > 20 else f"  {key}: {value}")
        return
    
    print("\n✅ All required environment variables are set!")
    
    from telegram.ext import ApplicationBuilder, MessageHandler, filters
    from handlers.command_handlers import register_command_handlers
    from handlers.message_handlers import handle_message
    from handlers.scheduled_tasks import schedule_tasks
    from services.scheduler_service import scheduler_service
    
    TOKEN = os.getenv('TELEGRAM_TOKEN')
    bot = ApplicationBuilder().token(TOKEN).build()
    register_command_handlers(bot)
    bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    schedule_tasks(bot)
    scheduler_service.schedule_jobs(bot.job_queue)
    print('🤖 Bot is running.')
    bot.run_polling()

if __name__ == "__main__":
    main()