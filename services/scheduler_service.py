import datetime
import random, os
import logging
import pytz
from telegram import Bot
from telegram.ext import ContextTypes

from services.weather_service import get_weather
from services.lyrics_service import lyrics_service
from services.user_service import user_service

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
SEND_MORNING_UPDATES = os.getenv('SEND_MORNING_UPDATES', True)
DEFAULT_CITY = os.getenv('DEFAULT_CITY', 'gothenburg')
TIMEZONE = os.getenv('TIMEZONE', 'Europe/Stockholm')

class SchedulerService:
    """Service for scheduling regular updates and messages"""
    
    def __init__(self):
        self.timezone = pytz.timezone(TIMEZONE)
        
    def schedule_jobs(self, job_queue):
        """Schedule all jobs"""
        if SEND_MORNING_UPDATES:
            job_time = datetime.time(hour=8, minute=00, tzinfo=self.timezone)
            job_queue.run_daily(self.send_morning_update, job_time)
            logger.info(f"Scheduled morning updates daily at 8:00 AM {TIMEZONE}")
        
        # Schedule other jobs here 
        
    async def send_morning_update(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a good morning message with updates"""
        now = datetime.datetime.now(self.timezone)
        date_str = now.strftime("%A, %d %B %Y")
        
        # Create morning greeting
        greeting_line = lyrics_service.get_greeting_line()
        
        morning_greetings = [
            f"God morgon! {greeting_line}",
            f"Tjena! En ny dag, {date_str}. {greeting_line}",
            f"Hej alla! {greeting_line}",
            f"God morgon, {date_str}! Jag röjer upp i chatten även idag! 🤖"
        ]
        greeting = random.choice(morning_greetings)
        
        # Get weather for default city
        weather_info = "Jag kan inte hämta väderinformation just nu."
        try:
            weather = get_weather(DEFAULT_CITY)
            if "Temperature:" in weather:
                temp = float(weather.split("Temperature: ")[1].split(" °C")[0])
                desc = weather.split("Description: ")[1].split("\n")[0]
                weather_info = f"Vädret i {DEFAULT_CITY}: {desc}, {temp:.1f}°C"
        except Exception as e:
            logger.error(f"Error getting weather for morning update: {e}")

        active_users = user_service.get_active_users(7)
        user_count = len(active_users)
        
        if user_count > 0:
            # Mention some active users occasionally
            if random.random() < 0.3 and user_count <= 7:  # 30% chance, small groups only
                user_names = [user_service.get_user_display_name(uid) for uid in list(active_users.keys())[:3]]
                personal_greeting = f"God morgon {', '.join(user_names)}!"
            else:
                personal_greeting = f"God morgon alla {user_count} aktiva chatmedlemmar!"
        else:
            personal_greeting = "God morgon!"

        message = f"{personal_greeting}\n\n{date_str}\n{weather_info}\n\nHa en bra dag! 🌞"
    

        
        try:
            await context.bot.send_message(chat_id=CHAT_ID, text=message)
            logger.info(f"Sent morning update to chat {CHAT_ID}")
        except Exception as e:
            logger.error(f"Failed to send morning update: {e}")

scheduler_service = SchedulerService()