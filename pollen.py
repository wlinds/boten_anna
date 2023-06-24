import requests
from bs4 import BeautifulSoup

def pollen_gbg():
    """Returns pollen data for Gothenburg"""

    feed_url = 'http://pollenrapporten.se/4.67f7c5a013d827ecb4c349/12.67f7c5a013d827ecb4c353.portlet?state=rss&sv.contenttype=text/xml;charset=UTF-8'

    # Fetch RSS feed
    response = requests.get(feed_url)
    rss_content = response.text

    # Parse RSS
    soup = BeautifulSoup(rss_content, 'xml')

    # Get feed info
    feed_title = soup.find('title').text
    feed_link = soup.find('link').text

    print('Feed Title:', feed_title)
    print('Feed Link:', feed_link)

    # Iterate over all entries
    entries = soup.find_all('item')

    for entry in entries:
        entry_title = entry.find('title').text
        entry_link = entry.find('link').text

        print('---')
        print('Entry Title:', entry_title)
        print('Entry Link:', entry_link)

    return entry_title, entry_link

if __name__ == '__main__':
    a, b = pollen_gbg()
    print('-------')
    print(a, b)
