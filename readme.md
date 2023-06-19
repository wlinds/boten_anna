<br><br>
<blockquote>

*Jag känner en bot, hon heter Anna, Anna heter hon\
Och hon kan banna, banna dig så hårt\
Hon röjer upp i våran kanal\
Jag vill berätta för dig, att jag känner en bot~*

</blockquote>
<br>

## **Boten Anna** 💁‍♀️

This Telegram group chat bot implement asynchronous functions, allowing for concurrent execution of multiple tasks without blocking the program's execution. The <a href="https://docs.python-telegram-bot.org/en/stable/telegram.ext.html">telegram.ext library</a> builds upon the <a href="https://docs.python.org/3/library/asyncio.html">asyncio library</a> to handle asynchronous operations. 

This approach enables the bot to handle multiple incoming updates concurrently, ensuring a seamless and responsive user experience.



## **Available commands**

| Command            | Description                                                                                         |
|--------------------|-----------------------------------------------------------------------------------------------------|
| `/hello`           | Greets the user.                                                                                    |
| `/roll {dice sides}`            | When members of a group have equal claims to something—such as a piece of loot or a chest— they can roll for it; the player who rolls the highest number is the winner. Defaults to 100.         |
| `/weather {city}`  | Get weather data through OpenWeatherMap API from any city.                                         |
| `/google {query}`  | Get search results for any query using bs4 webscraping as Google doesn't provide any search-related APIs.                                        |
| `/timer {seconds}`  | A timer, a companion in our quest to tame chaos and find moments of rest. It guards our tasks, swift and keen, empowering focus, a serene routine. **TODO:** Handle min and hours as well.          

## **Setup**

**1. Install neccessary depencencies:**
- json
- requests
- python-telegram-bot
- numpy
- bs4

**2. Get your keys and tokens:**
- Head over to <a href="https://openweathermap.org">OpenWeatherMap</a> to retrieve a free API key.


- Get your Telegram chat_id for the chat you want to add the bot to:
    - open web.telegram in browser
    - right click on the group name on the left menu
    - click 'inspect' button
    - you will see the group id in the attribute data-peer-id="-xxxxxxxxxx" or peer="-xxxxxxxxxx"

- With your Telegram account, execute <code>/new_bot</code> to user <code>@BotFather</code>. Copy the token to access the Telegram HTTP API.

**3. Create your json-file:**\
Create a json file and name it keys.json, add to the same directory as the Python script and fill in the information:

```
{
    "TOKEN": "your-token-string",
    "CHAT_ID": "00000000",
    "WEATHER": "your-openweathermap-api-key"
}
```

**4. Run main.py and start chatting with you new bot!**

# 🤖 - hellö


## **TODO**

- Print info to console when function is triggered by user

- Maybe add log files for later troubleshooting (prevent tedious debugging)

- Add more commands. Anything goes!


Look, Anna should know how to *"ban someone so hard"*, so we want to allow her to kick people from group chats.

If we look furher into the Anna lore, we find that she <a href="https://genius.com/Basshunter-boten-anna-lyrics">*"gör sig av med alla som spammar"*</a>, meaning she will get rid of spammers. Maybe set up some kind of threshold for messages per time unit before kicking?

- Maybe hook up an SQL table for user data, so she can remember stuff about users?

- Maybe add some other API?

- M̵̙͠a̸͓̕k̵̖̊e̴̛͚ ̵̤̈h̷͍̏e̵̗̕r̵̯͠ ̶̺͐s̴͕͝ḙ̷̌ṇ̸̔t̴̬͂i̴̫̍e̸̞̓n̵͉̽t̵̰̿