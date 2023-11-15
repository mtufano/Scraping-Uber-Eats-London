import os
import requests
from bs4 import BeautifulSoup

class URLCollector:

    def __init__(self, city_list_file, dir_path):
        self.__list = self.read_city_list(city_list_file)
        self.__dir = dir_path
        self.__failed_links = []

    def read_city_list(self, file_path):
        with open(file_path, 'r') as file:
            lines = [line.strip() for line in file]
        return lines

        

    def create_directory(self):
        if not os.path.exists(self.__dir):
            os.makedirs(self.__dir)
        self.collect_urls()
        self.log_failed_links()

    def collect_urls(self):
        all_urls = []
        for link in self.__list:
            try:
                reqs = requests.get(link)
                soup = BeautifulSoup(reqs.text, 'html.parser')

                for a_tag in soup.find_all('a'):
                    href = a_tag.get('href')
                    if href and href.startswith('/gb/store/'):
                        modified_href = 'https://www.ubereats.com' + href
                        all_urls.append(modified_href)
            except Exception as e:
                print(f"Failed to process {link}: {e}")
                self.__failed_links.append(link)

        # Write all URLs to a single file
        with open(os.path.join(self.__dir, "./data/london-rest-urls.txt"), "w", encoding='utf-8') as f:
            for url in all_urls:
                f.write(url + "\n")

    def log_failed_links(self):
        if self.__failed_links:
            with open(os.path.join(self.__dir, "failed_links.txt"), "w", encoding='utf-8') as f:
                for link in self.__failed_links:
                    f.write(link + "\n")

# Usage
dir_path = './'  
city_list_file = './data/london-categories.txt'  # Replace with the path to your file
url_collector = URLCollector(city_list_file, dir_path)
url_collector.create_directory()
