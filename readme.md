
## **Boten Anna** 💁‍♀️

This Telegram bot implement asynchronous functions, allowing for concurrent execution of multiple tasks without blocking the program's execution. The <a href="https://docs.python-telegram-bot.org/en/stable/telegram.ext.html">telegram.ext library</a> builds upon the <a href="https://docs.python.org/3/library/asyncio.html">asyncio library</a> to handle asynchronous operations. 

The library expects callback functions, such as <code>hello()</code> and <code>weather_command()</code>, to be defined as asynchronous functions. This approach enables the bot to handle multiple incoming updates concurrently, ensuring a seamless and responsive user experience.



## **Available commands**

| Command            | Description                                                                                         |
|--------------------|-----------------------------------------------------------------------------------------------------|
| `/hello`           | Greets the user.                                                                                    |
| `/roll`            | When members of a group have equal claims to something—such as a piece of loot, a chest, or a                    resource node—they will roll for it; the player who rolls the highest number is the winner.         |
| `/weather {city}`  | Get weather data through OpenWeatherMap API from any city.                                         |


## **Setup**

**1. Install neccessary depencencies:**
- json
- requests
- python-telegram-bot
- numpy

**2. Get your keys and tokens:**
- Head over to <a href="https://openweathermap.org">OpenWeatherMap</a> to retrieve a free API key.

- With your Telegram account, execute <code>/new_bot</code> to user <code>@BotFather</code>. Copy the token to access the Telegram HTTP API.

**3. Create your json-file:**\
Create a json file and name it keys.json, add to the same directory as the Python script and fill in the information:

```
{
    "TOKEN": "your-token-string",
    "WEATHER": "your-openweathermap-api-key"
}
```

**4. Run main.py and start chatting with you new bot!**

# 🤖 - hellö


