import time
import random
import requests
from bs4 import BeautifulSoup
import requests
from utils.env_utils import get_env_vars
import os


def welcome_message():
    """
    Generate a time-appropriate welcome message in Swedish. Legacy.
    
    Returns:
        str: A greeting message
    """
    current_hour = int(time.strftime('%H'))
    phrases = ['hej', 'tja', 'tjena', 'hallåj', 'tjabba', 'yo']

    if current_hour < 5 or current_hour >= 19:
        phrases = ['god kväll']
    elif 5 <= current_hour <= 9:
        phrases = ['god morgon']

    greeting = random.choice(phrases)
    return greeting.capitalize()


def google_search(query: str, verbose: bool = False) -> str:
    """
    Perform a Google search using the Custom Search API.
    
    Args:
        query (str): Search query
        verbose (bool): Whether to print debug info
        
    Returns:
        str: Formatted search results or error message
    """
    if not query:
        return "Please provide a search query."

    try:
        _, _, _, _, GOOGLE_API_KEY, _ = get_env_vars()
        GOOGLE_CSE_ID = os.getenv('GOOGLE_CSE_ID', '')
        
        if not GOOGLE_API_KEY or not GOOGLE_CSE_ID:
            return "Google Search API is not configured. Please set GOOGLE_API_KEY and GOOGLE_CSE_ID in the .env file."
        
        url = f'https://www.googleapis.com/customsearch/v1?q={query}&key={GOOGLE_API_KEY}&cx={GOOGLE_CSE_ID}'
        
        if verbose:
            print(f"Searching Google for: {query}")
            print(f"API URL: {url}")
        
        response = requests.get(url)
        
        if response.status_code != 200:
            return f"Error: API returned status code {response.status_code}"
        
        data = response.json()
        
        if 'items' not in data or not data['items']:
            return "No search results found for that query."
        
        # Format results
        results = []
        for i, item in enumerate(data['items'][:3]):  # Top 3 results
            results.append(f"{i+1}. {item['title']}\n   {item['link']}")
        
        formatted_results = "\n\n".join(results)
        return f"Top results for '{query}':\n\n{formatted_results}"

    except Exception as e:
        return f"Search error: {str(e)}"