from telegram.ext import ContextTypes
from services.nlp_service import save_chat_histories

async def save_data(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Regularly save chat histories"""
    save_chat_histories()
    print("Chat histories saved")

def schedule_tasks(bot):
    """Schedule periodic tasks"""
    job_queue = bot.job_queue
    job_queue.run_repeating(save_data, interval=3600)  # every hour
    
    return bot