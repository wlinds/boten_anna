import requests
from typing import Dict, Any
import json

with open('keys.json') as f:
    keys = json.load(f)
    GOOGLE_API_KEY = keys["GOOGLE"]

def get_pollen_forecast(latitude: float, longitude: float, days: int, api_key: str,
                        pageSize: int = 5, pageToken: str = None,
                        languageCode: str = "en", plantsDescription: bool = False) -> Dict[str, Any]:
    """
    Fetches pollen forecast data from the Pollen API.

    Args:
        latitude (float): Latitude of the location.
        longitude (float): Longitude of the location.
        days (int): Number of forecast days to request (minimum 1, maximum 5).
        api_key (str): Your API key for accessing the Pollen API.
        pageSize (int): Maximum number of daily info records to return per page.
                        Default is 5.
        pageToken (str): Page token received from a previous call.
        languageCode (str): Language code for the response. Default is "en".
        plantsDescription (bool): Whether to include plant descriptions. Default is False.

    Returns:
        Dict[str, Any]: Pollen forecast data.
    """

    endpoint = "https://pollen.googleapis.com/v1/forecast:lookup"
    params = {
        "location.latitude": latitude,
        "location.longitude": longitude,
        "days": days,
        "pageSize": pageSize,
        "pageToken": pageToken,
        "languageCode": languageCode,
        "plantsDescription": plantsDescription,
        "key": api_key  # Adding API key as a query parameter
    }

    response = requests.get(endpoint, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to fetch pollen forecast data: {response.text}")


def format_pollen_forecast(data):
    formatted_output = ""
    for daily_info in data['dailyInfo']:
        date = f"{daily_info['date']['year']}-{daily_info['date']['month']}-{daily_info['date']['day']}"
        formatted_output += f"Date: {date}\n"
        formatted_output += "Pollen Types:\n"
        for pollen_type in daily_info['pollenTypeInfo']:
            formatted_output += f"- {pollen_type['displayName']}:\n"
            if 'indexInfo' in pollen_type:
                formatted_output += f"  - Category: {pollen_type['indexInfo']['category']}\n"
                formatted_output += f"  - Description: {pollen_type['indexInfo']['indexDescription']}\n"
                if 'healthRecommendations' in pollen_type:
                    formatted_output += "  - Health Recommendations:\n"
                    for recommendation in pollen_type['healthRecommendations']:
                        formatted_output += f"    - {recommendation}\n"
        formatted_output += "\n"
    return formatted_output

if __name__ == "__main__":
    latitude = 57.689102
    longitude = 11.918963

    # Fetch forecast for 3 days
    pollen_forecast = get_pollen_forecast(latitude, longitude, days=3, api_key=GOOGLE_API_KEY)

    print(format_pollen_forecast(pollen_forecast))