import inspect
import json
import sqlite3
import logging
import os.path as path
from json import loads
from os import makedirs
from pathlib import Path
import validators
from bs4 import BeautifulSoup
from pandas import DataFrame, read_csv, concat
from requests import get, HTTPError
import concurrent.futures
import time
import random

# Setup logging
logging.basicConfig(format="%(asctime)s - [%(levelname)s]\t%(message)s",
                    datefmt='%d-%b-%y %H:%M:%S')

class Scraper:
    def __init__(self, url: str, base_dir: str = 'crawled_data',
                 f_name: str = 'crawled_data', menu_dir: str = 'menus'):
        self.url = url
        self.__details_json = None
        self.__bs4_data = None

        self.__restaurant_details = {}
        self.__restaurant_menu_details = []

        # Improved path handling
        self.__base_dir = Path(base_dir).resolve()
        self.__menu_dir = self.__base_dir / menu_dir
        self.__filename = f_name

        # Simplified URL validation and data fetching
        if not self.url_validator(url):
            logging.error(f"'{url}' is not a valid URL")
            return

        self.__bs4_data = self.fetch_details(url)
        if self.__bs4_data:
            self.__details_json = self.make_json(self.__bs4_data)
            if self.__details_json:
                self.fetch_restaurant_details(self.__details_json)
                self.fetch_restaurant_location()  # Ensure this is called
                self.__restaurant_menu_details = self.extract_menu_items(self.__details_json)  # Extract menu items here


    @staticmethod
    def url_validator(link: str) -> bool:
        return validators.url(link) and link.startswith('https://www.ubereats.com/')

    @staticmethod
    def fetch_details(url):
        try:
            raw = get(url, allow_redirects=True, headers=(
                {
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                                  '(KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36',
                }
            ))

            status_code = raw.status_code
            reason = raw.reason

            if status_code != 200:
                raise HTTPError(status_code, reason)

            bs4_data = BeautifulSoup(raw.content, 'lxml')
            return bs4_data

        except HTTPError as e:
            logging.error(f"{url} - {e.strerror} [{e.errno}]")
            return None

        except Exception as e:
            logging.debug(e)
            return None

    def make_json(self, bs4_data):
        try:
            elements = bs4_data.select('#__NEXT_DATA__')
            if not elements:  # Check if the list is empty
                logging.error("No elements found for #__NEXT_DATA__")
                return None

            data = elements[0].text
            details_json = loads(data)
            print(details_json)  # This will print the JSON for inspection
            return details_json

        except Exception as e:
            logging.error(e)
            return None



    # def fetch_restaurant_details(self, details_json):
    #     try:
    #         restaurant = details_json['props']['initialState']['menuPage']['menu']['meta']['restaurant']
    #         self.__restaurant_details['name'] = restaurant.get('name', 'Unknown Name').lower().replace(" ", "_")
    #         self.__restaurant_details['address'] = restaurant.get('location', {}).get('address', {}).get('address1', 'Unknown Address')
    #         self.__restaurant_details['neighborhood'] = restaurant.get('location', {}).get('address', {}).get('neighborhood', 'Unknown Neighborhood')
    #     except KeyError as e:
    #         logging.error(f"Key error while fetching restaurant details: {e}")
    #         self.__restaurant_details['name'] = 'Unknown Name'
    #         self.__restaurant_details['address'] = 'Unknown Address'
    #         self.__restaurant_details['neighborhood'] = 'Unknown Neighborhood'
    #     except Exception as e:
    #         logging.error(f"Error in fetch_restaurant_details: {e}")

    # def fetch_restaurant_location(self):
    #     try:
    #         restaurant_location = self.__details_json['props']['initialState']['menuPage']['menu']['meta']['customerLocation']
    #         self.__restaurant_details['lat'] = restaurant_location.get('lat', 'Unknown Latitude')
    #         self.__restaurant_details['lon'] = restaurant_location.get('lon', 'Unknown Longitude')
    #         self.__restaurant_details['city'] = restaurant_location.get('city', 'Unknown City')
    #         self.__restaurant_details['neighborhood'] = restaurant_location.get('neighborhood', 'Unknown Neighborhood')
    #         self.__restaurant_details['postcode'] = restaurant_location.get('postcode', 'Unknown Postcode')
    #         self.__restaurant_details['cityId'] = restaurant_location.get('cityId', 'Unknown City ID')
    #         self.__restaurant_details['zoneId'] = restaurant_location.get('zoneId', 'Unknown Zone ID')
    #         self.__restaurant_details['geohash'] = restaurant_location.get('geohash', 'Unknown Geohash')

    #     except KeyError as e:
    #         logging.error(f"Key error while fetching restaurant location: {e}")
    #         # Set default values for all location details in case of KeyError
    #         self.__restaurant_details.update({
    #             'lat': 'Unknown Latitude',
    #             'lon': 'Unknown Longitude',
    #             'city': 'Unknown City',
    #             'neighborhood': 'Unknown Neighborhood',
    #             'postcode': 'Unknown Postcode',
    #             'cityId': 'Unknown City ID',
    #             'zoneId': 'Unknown Zone ID',
    #             'geohash': 'Unknown Geohash'
    #         })

    #     except Exception as e:
    #         logging.error(f"Error in fetch_restaurant_location: {e}")


    # def extract_menu_items(self, details_json):
    #     menu_items = details_json['props']['initialState']['menuPage']['menu']['meta']['items']
    #     menu_data = []

    #     for item in menu_items:
    #         try:
    #             name = item.get('name', 'No Name')
    #             description = item.get('description', 'No Description')
    #             price = item.get('price', {}).get('formatted', 'No Price').replace('AED\xa0', '')
    #             image_data = item.get('image')
    #             image_url = image_data.get('url') if image_data else 'No Image URL'

    #             menu_data.append({
    #                 'name': name,
    #                 'description': description,
    #                 'price': price,
    #                 'image_url': image_url    
    #             })
    #         except KeyError as e:
    #             logging.error(f"Key error while fetching menu item: {e}")
    #             continue  # Skip this item and continue with the next
    #         except Exception as e:
    #             logging.error(f"Error in extract_menu_items: {e}")
    #             continue  # Skip this item and continue with the next

    #     return menu_data
    
    # def save_to_db(self, db_name: str):
    #     try:
    #         # Create or connect to a SQLite database
    #         with sqlite3.connect(db_name) as conn:
    #             c = conn.cursor()

    #             # Create tables if they don't exist
    #             c.execute('''CREATE TABLE IF NOT EXISTS restaurant (
    #                             id INTEGER PRIMARY KEY,
    #                             name TEXT,
    #                             address TEXT,
    #                             neighborhood TEXT,
    #                             lat REAL,
    #                             lon REAL,
    #                             city TEXT,
    #                             postcode TEXT,
    #                             cityId INTEGER,
    #                             zoneId INTEGER,
    #                             geohash TEXT
    #                         )''')

    #             c.execute('''CREATE TABLE IF NOT EXISTS menu (
    #                             id INTEGER PRIMARY KEY,
    #                             restaurant_id INTEGER,
    #                             name TEXT,
    #                             description TEXT,
    #                             price TEXT,
    #                             image_url TEXT,
    #                             FOREIGN KEY (restaurant_id) REFERENCES restaurant (id)
    #                         )''')

    #             # Insert restaurant details
    #             c.execute('''INSERT INTO restaurant 
    #                          (name, address, neighborhood, lat, lon, city, postcode, cityId, zoneId, geohash) 
    #                          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
    #                       (self.__restaurant_details['name'], self.__restaurant_details['address'],
    #                        self.__restaurant_details['neighborhood'], self.__restaurant_details['lat'],
    #                        self.__restaurant_details['lon'], self.__restaurant_details['city'],
    #                        self.__restaurant_details['postcode'], self.__restaurant_details['cityId'],
    #                        self.__restaurant_details['zoneId'], self.__restaurant_details['geohash']))
    #             restaurant_id = c.lastrowid

    #             # Insert menu items
    #             for item in self.__restaurant_menu_details:
    #                 c.execute('INSERT INTO menu (restaurant_id, name, description, price, image_url) VALUES (?, ?, ?, ?, ?)',
    #                           (restaurant_id, item['name'], item['description'], item['price'], item['image_url']))

    #             # Commit is handled automatically by the context manager

    #     except sqlite3.Error as e:
    #         logging.error(f"SQLite error: {e}")
    #         # Optionally, handle or re-raise

    #     except Exception as e:
    #         logging.error(f"General error in save_to_db: {e}")
    #         # Optionally, handle or re-raise


# Function to read URLs from a file
def read_urls_from_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:  # Specify UTF-8 encoding here
        lines = [line.strip() for line in file]
    #print(lines)
    return lines
    
# Function to handle scraping for a single URL
def scrape_single_url(url, db_name):
    try:
        # Replace '=ASAP' with '=anytime' in the URL
        url = url.replace('=ASAP', '=anytime')

        scraper = Scraper(url)
        #scraper.save_to_db(db_name)

        # Introduce a random delay between requests to mimic human behavior and reduce server load
        time.sleep(random.uniform(1, 3))  # Random delay between 1 and 3 seconds

    except Exception as e:
        logging.error(f"Failed to scrape {url}: {e}")
        return url  # Return the URL that failed

def scrape_urls(file_path, db_name):
    urls = read_urls_from_file(file_path)
    for url in urls:
        try:
            scrape_single_url(url, db_name)
            # Introduce a delay between requests
            time.sleep(random.uniform(1, 3))
        except Exception as e:
            logging.error(f"Failed to scrape {url}: {e}")

# Example usage
input_file = "./data/london-rest-urls.txt"  # Path to the file containing URLs
scrape_urls(input_file, "ubereats_london.db")

    # # Define the maximum number of threads
    # MAX_THREADS = 50  # Start with a lower number and adjust as needed

    # # Using ThreadPoolExecutor to create and manage threads
    # with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
    #     # Start the load operations and mark each future with its URL
    #     future_to_url = {executor.submit(scrape_single_url, url, db_name): url for url in urls}

    #     for future in concurrent.futures.as_completed(future_to_url):
    #         url = future_to_url[future]
    #         try:
    #             # Retrieve result (if any exception occurred, it will be raised here)
    #             result = future.result()
    #             if result:
    #                 failed_urls.append(result)
    #         except Exception as exc:
    #             logging.error(f'{url} generated an exception: {exc}')

    # # Optionally, save the failed URLs to a file or handle them as needed
    # with open('failed_urls_multithreaded.txt', 'w') as file:
    #     for url in failed_urls:
    #         file.write(url + '\n')


