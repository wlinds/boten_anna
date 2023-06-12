import time, random
from bs4 import BeautifulSoup
import requests, json

def welcome_message():
    current_hour = int(time.strftime('%H'))
    phrases = ['hej', 'tja', 'tjena', 'hallåj', 'tjabba', 'yo']

    if current_hour < 5 or current_hour >= 19:
        phrases = ['god kväll']
    elif 5 <= current_hour <= 9:
        phrases = ['god morgon']

    greeting = random.choice(phrases)
    return greeting.capitalize()


def google_search(query, verbose=False):
    headers = {
        'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36'
    }

    html = requests.get(f'https://www.google.com/search?q={query}', headers=headers).text
    soup = BeautifulSoup(html, 'lxml')

    div_elements = soup.find_all('div', class_='tF2Cxc')
    if div_elements:
        # Loop through the div elements and print the links
        for div_element in div_elements:
            link = div_element.a['href']
            return link
            if verbose:
                print(link)
    else:
        print("No search results found.")

if __name__ == "__main__":
    google_search("Sweden")