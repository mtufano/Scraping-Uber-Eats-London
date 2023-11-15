import requests
from bs4 import BeautifulSoup
import pandas as pd
import json

class Scraper:
    def __init__(self, url: str):
        self.url = url
        self.restaurant_info = {}
        self.menu_items = []

    def fetch_and_parse(self):
        try:
            response = requests.get(self.url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                              '(KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36'
            })
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            return soup
        except requests.HTTPError as e:
            print(f"HTTP Error: {e}")
        except Exception as e:
            print(f"Error: {e}")

    def extract_data(self, soup):
        script_tags = soup.find_all('script')
        for script in script_tags:
            if 'application/ld+json' in str(script):
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict) and 'name' in data and 'address' in data:
                        self.restaurant_info = data
                    elif isinstance(data, list):
                        for item in data:
                            if item.get('@type') == 'MenuItem':
                                self.menu_items.append(item)
                except json.JSONDecodeError:
                    continue

    def save_to_csv(self, filename):
        df = pd.DataFrame(self.menu_items)
        df.to_csv(filename, index=False)
        print(f"Data saved to {filename}")

# Example usage
# URL of the webpage you want to scrape
url = 'https://www.ubereats.com/gb/store/chicken-hub-holborn/Yr2-CV8-SG-YEBh7yi44Lg?diningMode=DELIVERY'
scraper = Scraper(url)
soup = scraper.fetch_and_parse()
if soup:
    scraper.extract_data(soup)
    scraper.save_to_csv('menu_items.csv')


