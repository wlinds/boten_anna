import requests
import xml.etree.ElementTree as ET
import schedule

def sr_test():
    print('Checking for new episodes...')
    response = requests.get('http://api.sr.se/api/v2/news/episodes')
    xml_data = response.content

    # Parse XML
    root = ET.fromstring(xml_data)

    # Find episode
    episode_elements = root.findall('.//episode')

    if len(episode_elements) == 0:
        print('No new content found.')
        return

    print(f'Found {len(episode_elements)} new episode(s):')

    for episode_element in episode_elements:
        description = episode_element.find('description').text
        url = episode_element.find('url').text

        print('---')
        print('Description:', description)
        print('URL:', url)

    print('---')


if __name__ == '__main__':
    # Schedule the job to run every hour
    schedule.every().hour.do(sr_test)
    
    print('SR Script is running. Checking for new episodes every hour.')
    
    # Keep the script running indefinitely
    while True:
        schedule.run_pending()