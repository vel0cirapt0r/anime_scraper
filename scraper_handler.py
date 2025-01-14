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

    def find_season_episodes_from_page(self, season_page_link, episode_folder_path):
        episodes = list()
        response = requests.get(season_page_link)
        soup = BeautifulSoup(response.text, 'html.parser')
        result_episodes = soup.find_all('div', attrs={"class": 'Singamdasam'})

        for episode in result_episodes:
            # Find the single <a> tag within the current <div>
            a_tag = episode.find("a")
            if a_tag:  # Ensure <a> tag exists
                episode_link = "https:" + a_tag.get("href")

                # Check for '/<number> ' pattern
                match_file_number = re.search(r"/(\d+)\s", episode_link)
                if match_file_number:
                    # print(episode_link)
                    episode_item = self.get_episode_item(
                        episode_info_link=episode_link,
                        episode_folder_path=episode_folder_path
                    )
                    episodes.append(episode_item)
                    continue  # Skip further checks for this link

                # Check for 'Episode-' or 'Season-' pattern
                match_episode_season = re.search(r"(?:Episode-|Season-)(\d+)", episode_link, re.IGNORECASE)
                if match_episode_season:
                    # print(episode_link)
                    episode_item = self.get_episodes_info_url(
                        episode_link=episode_link,
                        episode_folder_path=episode_folder_path
                    )
                    episodes.append(episode_item)


        return episodes

    def scrape_episodes_of_season(self, season_item):

        full_path = season_item.season_folder_path
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

                    episodes_in_page = self.find_season_episodes_from_page(season_page_link=season_page_link,
                                                                           episode_folder_path=full_path)
                    for episode in episodes_in_page:
                        episodes.append(episode)

        except:
            episodes = self.find_season_episodes_from_page(
                season_page_link=season_item.season_url,
                episode_folder_path=full_path
            )

        return episodes

    def get_episodes_info_url(self, episode_link, episode_folder_path):
        episode_item = None  # Default value

        response = requests.get(episode_link)

        # Parse the HTML with BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all <div class="Singamdasam"> elements
        singamdasam_divs = soup.find_all('div', class_='Singamdasam')

        links = []

        # Loop through each <div> to extract the links and file sizes
        for div in singamdasam_divs:
            # print(div)
            # print("#" * 50)
            # Find the <a> tag and the size span
            a_tag = div.find('a')
            size_span = div.find('span', text=lambda x: x and 'Size:' in x)

            if a_tag and size_span:
                # Extract the size value
                size_text = size_span.find_next_sibling(text=True)
                if size_text:
                    # Remove "MB" and convert size to float for comparison
                    size_value = float(size_text.replace('MB', '').strip())
                    if size_value > 0:  # Only add links with size > 0 MB
                        links.append("https:" + a_tag['href'])

        # Print the extracted links
        for link in links:
            # print(f"Link: {link}")
            episode_item = self.get_episode_item(
                episode_info_link=link,
                episode_folder_path=episode_folder_path
            )

        return episode_item

    def get_episode_item(self, episode_info_link, episode_folder_path):
        response = requests.get(episode_info_link)
        # print(response.status_code, response.url)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Base URL for constructing the full link
        base_url = "https://eng.cartoonsarea.cc"

        # Find the anchor tag with class 'download-btn'
        download_link = soup.find('a', class_='download-btn')

        if download_link and 'href' in download_link.attrs:
            # Construct the full download URL
            full_download_url = urljoin(base_url, download_link['href'])
            # print(full_download_url)

            # Extract season number from the URL
            season_match = re.search(r"[Ss]eason[\s\-]*(\d+)", episode_info_link)
            season_number = int(season_match.group(1)) if season_match else None

            # Extract episode number from the URL
            episode_number_match = re.search(r"Episode\s(\d+)", episode_info_link, re.IGNORECASE)
            if not episode_number_match:
                # If "Episode X" is not found, look for "X " after "Episode"
                episode_number_match = re.search(r"/(\d+)\s", episode_info_link)

            episode_number = int(episode_number_match.group(1)) if episode_number_match else None

            # Extract episode name from the download URL
            episode_name_match = re.search(r"/\d+\s(.+?)\.mp4", full_download_url, re.IGNORECASE)
            episode_name = (
                episode_name_match.group(1).replace('%20', ' ').replace('!', '')
                if episode_name_match else "Unknown"
            )

            # Create and return the Episode object
            episode = Episode(
                episode_number=episode_number,
                episode_name=episode_name,
                episode_url=full_download_url,
                episode_folder_path=episode_folder_path,
                season_number=season_number
            )
            return episode
        else:
            print("No download link found.")
            return None
