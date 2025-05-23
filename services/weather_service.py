import requests
import os

def get_weather(city):
    """
    Get weather information for a specified city.
    
    Args:
        city (str): City name
        
    Returns:
        str: Formatted weather information
    """
    if not city:
        return "Please provide a city or region."

    # Get API key when needed, not at import time
    weather_key = os.getenv('OPENWEATHERMAP_API_KEY')
    if not weather_key:
        return "Weather service not configured. Missing OPENWEATHERMAP_API_KEY."

    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={weather_key}"
    
    try:
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
            return weather_info
        else:
            return f"Failed to retrieve weather information for {city}."
    except Exception as e:
        return f"Error fetching weather data: {str(e)}"