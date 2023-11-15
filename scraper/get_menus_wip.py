import requests
from bs4 import BeautifulSoup
import pandas as pd
import json

class Scraper:
    def __init__(self, url: str):
        self.url = url

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
    
    def extract_menu_data(self, soup):
        menu_items = []
        script_tags = soup.find_all('script')
        for script in script_tags:
            if 'application/ld+json' in str(script):
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict) and 'hasMenu' in data:
                        menu_sections = data['hasMenu']['hasMenuSection']
                        for section in menu_sections:
                            for item in section['hasMenuItem']:
                                menu_items.append({
                                    'Name': item['name'],
                                    'Description': item.get('description', ''),
                                    'Price': item['offers']['price'],
                                    'Currency': item['offers']['priceCurrency']
                                })
                except json.JSONDecodeError:
                    continue
        return menu_items
    
    def extract_restaurant_info(self, soup):
        script_tags = soup.find_all('script')
        for script in script_tags:
            if 'application/ld+json' in str(script):
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict) and data.get('@type') == 'Restaurant':
                        return data
                except json.JSONDecodeError:
                    continue
        return None
    
    def save_to_csv(self, menu_items, filename):
        if menu_items:
            df = pd.DataFrame(menu_items)
            df.to_csv(filename, index=False)
            print(f"Data saved to {filename}")
        else:
            print("No data to save")

    def save_restaurant_to_csv(self, data, filename):
        if data:
            # Extracting address and geo data
            address = data['address']
            geo = data['geo']

            restaurant_info = {
                'Name': data['name'],
                'Cuisine': ', '.join(data['servesCuisine']),
                'Address': ', '.join([address.get(key, '') for key in ['streetAddress', 'addressLocality', 'addressRegion', 'postalCode', 'addressCountry']]),
                'Latitude': geo['latitude'],
                'Longitude': geo['longitude'],
                'Rating': data['aggregateRating']['ratingValue'],
                'ReviewCount': data['aggregateRating']['reviewCount']
            }

            df = pd.DataFrame([restaurant_info])
            df.to_csv(filename, index=False)
            print(f"Restaurant data saved to {filename}")
        else:
            print("No restaurant data to save")


# Example usage
# URL of the webpage you want to scrape
url = 'https://www.ubereats.com/gb/store/sticksnsushi-soho/YQeBq78eUNyu_c5ZMBo_YQ?diningMode=DELIVERY&pl=JTdCJTIyYWRkcmVzcyUyMiUzQSUyMkJhcm5ldCUyMiUyQyUyMnJlZmVyZW5jZSUyMiUzQSUyMkNoSUpVNUJkbjBjWGRrZ1JrSC1SMGNpRkVRbyUyMiUyQyUyMnJlZmVyZW5jZVR5cGUlMjIlM0ElMjJnb29nbGVfcGxhY2VzJTIyJTJDJTIybGF0aXR1ZGUlMjIlM0E1MS42NTY5MjI1JTJDJTIybG9uZ2l0dWRlJTIyJTNBLTAuMTk0OTI1MiU3RA%3D%3D'
scraper = Scraper(url)
soup = scraper.fetch_and_parse()
if soup:
    menu_items = scraper.extract_menu_data(soup)
    restaurant_data = scraper.extract_restaurant_info(soup)
    scraper.save_restaurant_to_csv(restaurant_data, 'restaurant_info.csv')
    scraper.save_to_csv(menu_items, 'menu.csv')
else:
    print("Failed to fetch or parse the webpage")

