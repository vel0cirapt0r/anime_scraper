import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re

from models import Season, Episode


class ScraperHandler:
    def __init__(self, anime_url):
        self.anime_url = anime_url

    def scrap_seasons(self):
        parent_folder = "one-piece"

        # Create the parent folder
        try:
            os.mkdir(parent_folder)
            # print(f"Folder '{parent_folder}' created successfully.")
        except FileExistsError:
            print(f"Folder '{parent_folder}' already exists.")
        except Exception as e:
            print(f"An error occurred: {e}")

        response = requests.get(self.anime_url)

        # print(response.status_code)

        soup = BeautifulSoup(response.text, 'html.parser')

        result_seasons = soup.find_all('div', attrs={"class": 'Singamdasam'})

        season_items = list()

        for season in result_seasons:
            # Find the single <a> tag within the current <div>
            a_tag = season.find("a")
            if a_tag:  # Ensure <a> tag exists
                season_link = "https:" + a_tag.get("href")

            else:
                continue

            # Regular expression to find 'season-' followed by a number
            match = re.search(r"season-(\d+)", season_link, re.IGNORECASE)

            if match:
                season_number = int(match.group(1))  # Extract the number after 'season-'

                # print(season_number)
                new_folder_name = str(season_number)
                full_path = os.path.join(parent_folder, new_folder_name)

                season = Season(
                    season_number=season_number,
                    season_url=season_link,
                    season_folder_path=full_path
                )

                season_items.append(season)

            else:
                pass

        print(f"this anime has {len(season_items)} seasons available.")

        return season_items

    def find_season_episodes_from_page(self, season_page_link):
        episodes = list()
        response = requests.get(season_page_link)
        # print(response.url)
        soup = BeautifulSoup(response.text, 'html.parser')
        result_episodes = soup.find_all('div', attrs={"class": 'Singamdasam'})

        for episode in result_episodes:
            # Find the single <a> tag within the current <div>
            a_tag = episode.find("a")
            if a_tag:  # Ensure <a> tag exists
                episode_link = "https:" + a_tag.get("href")
                # print(episode_link)
            else:
                continue

            # Regular expression to find 'season-' followed by a number
            matches = re.findall(r"(?:Episode|Season)-(\d+)", episode_link, re.IGNORECASE)

            if matches:
                episode_number = int(matches[-1])  # Extract the number after 'season-'
                # if episode_number not in episodes:
                # episode = self.get_episodes_info_url(episode_link)
                episodes.append(episode_number)

        return episodes

    def scrape_episodes_of_season(self, season_item):

        full_path = season_item.season_folder_path
        parent_folder, new_folder_name = full_path.split("/")

        # Create the new folder for each season in the one-piece folder
        try:
            os.mkdir(full_path)
            # print(f"Folder '{new_folder_name}' created inside '{parent_folder}'.")
        except FileExistsError:
            print(f"Folder '{new_folder_name}' already exists in '{parent_folder}'.")
        except Exception as e:
            print(f"An error occurred: {e}")

        response = requests.get(season_item.season_url)
        # print(response.url)
        soup = BeautifulSoup(response.text, "html.parser")

        try:
            page_tag = soup.find('ul', attrs={"class": "pagination"})

            pages = page_tag.find_all('li')

            episodes = list()

            for page in pages:
                # Find the single <a> tag within the current <div>
                a_tag = page.find("a")
                if a_tag:  # Ensure <a> tag exists
                    season_page_link = season_item.season_url + a_tag.get("href")
                    # print(season_page_link)

                    episodes_in_page = self.find_season_episodes_from_page(season_page_link=season_page_link)
                    for episode in episodes_in_page:
                        episodes.append(episode)

        except:
            episodes = self.find_season_episodes_from_page(season_page_link=season_item.season_url)

        return episodes

    def get_episodes_info_url(self, episode_link):
        response = requests.get(episode_link)

        soup = BeautifulSoup(response.text, 'html.parser')

        # Base URL for constructing the full link
        base_url = "https://eng.cartoonsarea.cc"

        # Find all <div> tags with class "Singamdasam"
        divs = soup.find_all('div', class_='Singamdasam')

        # Iterate through each <div> and look for file size greater than zero
        for div in divs:
            size_text = div.get_text()
            # Check if the size is greater than zero (size is assumed to be in format 'XX.XXMB')
            if "Size:" in size_text and "0.00MB" not in size_text:
                link_tag = div.find('a', href=True)
                if link_tag:
                    # Construct the full URL
                    full_url = urljoin(base_url, link_tag['href'])
                    print("Full Download URL:", full_url)
                    break  # Stop after finding the first matching link

    def get_episode_download_url(self, episode_info_link):
        response = requests.get(episode_info_link)
        # Parse the HTML content with BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')

        # Base URL for constructing the full link
        base_url = "https://eng.cartoonsarea.cc"

        # Find the anchor tag with class 'download-btn'
        download_link = soup.find('a', class_='download-btn')

        # Construct the full download URL
        if download_link and 'href' in download_link.attrs:
            full_download_url = urljoin(base_url, download_link['href'])
            print("Full Download URL:", full_download_url)
        else:
            print("No download link found.")
