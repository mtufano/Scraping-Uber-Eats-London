import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import sqlite3
import logging
import time
import random
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

    def save_to_db(self, db_name: str, restaurant_data, menu_items):
        try:
            with sqlite3.connect(db_name) as conn:
                c = conn.cursor()

                # Create restaurant table with a combined 'Address' field
                c.execute('''CREATE TABLE IF NOT EXISTS restaurant (
                                id INTEGER PRIMARY KEY,
                                name TEXT,
                                cuisine TEXT,
                                address TEXT,
                                latitude REAL,
                                longitude REAL,
                                rating REAL,
                                review_count INTEGER
                            )''')

                # Extracting address and geo data
                address = restaurant_data['address']
                geo = restaurant_data['geo']

                # Combine address components into a single 'Address' field
                full_address = ', '.join([address.get(key, '') for key in ['streetAddress', 'addressLocality', 'addressRegion', 'postalCode', 'addressCountry']])

                # Insert restaurant data
                c.execute('''INSERT INTO restaurant 
                            (name, cuisine, address, latitude, longitude, rating, review_count) 
                            VALUES (?, ?, ?, ?, ?, ?, ?)''',
                        (restaurant_data['name'], ', '.join(restaurant_data['servesCuisine']),
                        full_address, geo['latitude'], geo['longitude'],
                        restaurant_data['aggregateRating']['ratingValue'],
                        restaurant_data['aggregateRating']['reviewCount']))
                
                # Create menu table if it doesn't exist
                c.execute('''CREATE TABLE IF NOT EXISTS menu (
                                id INTEGER PRIMARY KEY,
                                restaurant_id INTEGER,
                                name TEXT,
                                description TEXT,
                                price REAL,
                                currency TEXT,
                                FOREIGN KEY (restaurant_id) REFERENCES restaurant (id)
                            )''')

                # Get the last inserted restaurant id
                restaurant_id = c.lastrowid

                # Insert menu items
                for item in menu_items:
                    c.execute('''INSERT INTO menu 
                                 (restaurant_id, name, description, price, currency) 
                                 VALUES (?, ?, ?, ?, ?)''',
                              (restaurant_id, item['Name'], item['Description'],
                               item['Price'], item['Currency']))

        except sqlite3.Error as e:
            logging.error(f"SQLite error: {e}")
            # Optionally, handle or re-raise

        except Exception as e:
            logging.error(f"General error in save_to_db: {e}")
            # Optionally, handle or re-raise



# Function to read URLs from a file
def read_urls_from_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return [line.strip() for line in file.readlines()] 
    
def scrape_single_url(url, db_name):
    try:
        scraper = Scraper(url)
        soup = scraper.fetch_and_parse()
        if soup:
            menu_items = scraper.extract_menu_data(soup)
            restaurant_data = scraper.extract_restaurant_info(soup)
            if restaurant_data and menu_items:
                scraper.save_to_db(db_name, restaurant_data, menu_items)
            else:
                print(f"No data extracted from {url}")
        else:
            print(f"Failed to fetch or parse the webpage: {url}")
        time.sleep(random.uniform(1, 3))
    except Exception as e:
        logging.error(f"Failed to scrape {url}: {e}")
        return url

# Modified function to scrape URLs using multithreading
def scrape_urls(file_path, db_name):
    urls = read_urls_from_file(file_path)
    failed_urls = []

    # Define the maximum number of threads
    MAX_THREADS = 15  # Start with a lower number and adjust as needed

    # Using ThreadPoolExecutor to create and manage threads
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        # Start the load operations and mark each future with its URL
        future_to_url = {executor.submit(scrape_single_url, url, db_name): url for url in urls}

        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                # Retrieve result (if any exception occurred, it will be raised here)
                result = future.result()
                if result:
                    failed_urls.append(result)
            except Exception as exc:
                logging.error(f'{url} generated an exception: {exc}')

        with open('failed_urls_multithreaded.txt', 'w', encoding='utf-8') as file:
            for url in failed_urls:
                file.write(url + '\n')

# Example usage
input_file = "./data/test.txt"  # Path to the file containing URLs
scrape_urls(input_file, "uber_test.db")


# # URL of the webpage you want to scrape
# url = 'https://www.ubereats.com/gb/store/sticksnsushi-soho/YQeBq78eUNyu_c5ZMBo_YQ?diningMode=DELIVERY&pl=JTdCJTIyYWRkcmVzcyUyMiUzQSUyMkJhcm5ldCUyMiUyQyUyMnJlZmVyZW5jZSUyMiUzQSUyMkNoSUpVNUJkbjBjWGRrZ1JrSC1SMGNpRkVRbyUyMiUyQyUyMnJlZmVyZW5jZVR5cGUlMjIlM0ElMjJnb29nbGVfcGxhY2VzJTIyJTJDJTIybGF0aXR1ZGUlMjIlM0E1MS42NTY5MjI1JTJDJTIybG9uZ2l0dWRlJTIyJTNBLTAuMTk0OTI1MiU3RA%3D%3D'
# scraper = Scraper(url)
# soup = scraper.fetch_and_parse()
# if soup:
#     menu_items = scraper.extract_menu_data(soup)
#     restaurant_data = scraper.extract_restaurant_info(soup)
#     scraper.save_to_db('test.db', restaurant_data, menu_items)
# else:
#     print("Failed to fetch or parse the webpage")

