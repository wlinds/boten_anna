import requests
import json
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime
from utils.env_utils import get_env_vars

_, _, _, _, GOOGLE_API_KEY, _ = get_env_vars()

@dataclass
class PollenLocation:
    city: str
    latitude: float
    longitude: float

LOCATIONS = {
    "gothenburg": PollenLocation("Gothenburg", 57.689102, 11.918963),
    "stockholm": PollenLocation("Stockholm", 59.329323, 18.068581),
    "malmo": PollenLocation("Malmö", 55.604981, 13.003822),
}

def get_pollen_forecast(location: PollenLocation, days: int = 3) -> Dict[str, Any]:
    """
    Fetches pollen forecast data from the Google Pollen API.
    
    Args:
        location (PollenLocation): Location object with coordinates
        days (int): Number of forecast days (1-5)
        
    Returns:
        Dict[str, Any]: Pollen forecast data
    """
    if not GOOGLE_API_KEY:
        return {"error": "Google API key not configured"}
    
    endpoint = "https://pollen.googleapis.com/v1/forecast:lookup"
    params = {
        "location.latitude": location.latitude,
        "location.longitude": location.longitude,
        "days": min(days, 5),  # Maximum 5 days
        "languageCode": "en",
        "key": GOOGLE_API_KEY
    }
    
    try:
        response = requests.get(endpoint, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"API error: {response.status_code}", "details": response.text}
    except Exception as e:
        return {"error": f"Request failed: {str(e)}"}

def get_emoji_for_category(category: str) -> str:
    """Get an appropriate emoji for the pollen level category"""
    category_emojis = {
        "NONE": "✅",
        "LOW": "🟢",
        "MEDIUM": "🟡",
        "HIGH": "🟠",
        "VERY_HIGH": "🔴"
    }
    return category_emojis.get(category, "❓")

def format_date(date_dict: Dict[str, int]) -> str:
    """Format the date from API response to human-readable format"""
    try:
        date_obj = datetime(
            year=date_dict.get('year', 2000),
            month=date_dict.get('month', 1),
            day=date_dict.get('day', 1)
        )
        return date_obj.strftime("%A, %B %d, %Y")
    except:
        return f"{date_dict.get('year', '??')}-{date_dict.get('month', '??')}-{date_dict.get('day', '??')}"

def format_pollen_forecast(data: Dict[str, Any], location_name: str) -> str:
    """
    Format the pollen forecast data into a readable message
    
    Args:
        data (Dict[str, Any]): Pollen data from the API
        location_name (str): Name of the location
        
    Returns:
        str: Formatted message
    """
    if "error" in data:
        return f"Error getting pollen data: {data['error']}"
    
    if "dailyInfo" not in data or not data["dailyInfo"]:
        return f"No pollen information available for {location_name}."
    
    formatted_output = f"🌼 Pollen Forecast for {location_name} 🌼\n\n"
    
    for daily_info in data['dailyInfo']:
        date = format_date(daily_info['date'])
        formatted_output += f"📅 {date}\n"
        
        if 'pollenTypeInfo' not in daily_info or not daily_info['pollenTypeInfo']:
            formatted_output += "No pollen data available for this day.\n\n"
            continue
        
        for pollen_type in daily_info['pollenTypeInfo']:
            pollen_name = pollen_type.get('displayName', 'Unknown')
            
            if 'indexInfo' in pollen_type:
                category = pollen_type['indexInfo'].get('category', 'UNKNOWN')
                emoji = get_emoji_for_category(category)
                formatted_output += f"{emoji} {pollen_name}: {category.title()}\n"
                
                # Add health recommendations if available
                if 'healthRecommendations' in pollen_type and pollen_type['healthRecommendations']:
                    # Just include the first recommendation to keep it concise
                    formatted_output += f"   ℹ️ {pollen_type['healthRecommendations'][0]}\n"
            else:
                formatted_output += f"❓ {pollen_name}: No data available\n"
        
        formatted_output += "\n"
    
    # Summary
    highest_categories = []
    highest_pollen_types = []
    
    # Find the highest pollen levels
    for daily_info in data['dailyInfo'][:1]:  # Just look at today's data for summary
        if 'pollenTypeInfo' in daily_info:
            for pollen_type in daily_info['pollenTypeInfo']:
                if 'indexInfo' in pollen_type:
                    category = pollen_type['indexInfo'].get('category', '')
                    if category in ['HIGH', 'VERY_HIGH'] and category not in highest_categories:
                        highest_categories.append(category)
                        highest_pollen_types.append(pollen_type.get('displayName', 'Unknown'))
    
    if highest_pollen_types:
        formatted_output += f"⚠️ Today's alert: High levels of {', '.join(highest_pollen_types)}.\n"
        formatted_output += "Take appropriate precautions if you're sensitive to these allergens."
    else:
        formatted_output += "✅ Good news! No high pollen levels detected today."
    
    return formatted_output

def get_pollen_for_location(location_name: str = "gothenburg", days: int = 3) -> str:
    """
    Get pollen forecast for a specified location
    
    Args:
        location_name (str): Name of the location (case insensitive)
        days (int): Number of days to forecast
        
    Returns:
        str: Formatted pollen information
    """
    location_key = location_name.lower()
    
    # Default to Gothenburg if location not found
    if location_key not in LOCATIONS:
        return f"Location '{location_name}' not found. Available locations: {', '.join(LOCATIONS.keys())}"
    
    location = LOCATIONS[location_key]
    forecast_data = get_pollen_forecast(location, days)
    return format_pollen_forecast(forecast_data, location.city)