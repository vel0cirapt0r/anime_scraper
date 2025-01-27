import os

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re

from db_manager import (
    add_episode,
    add_season,
    add_anime,
    mark_episode_as_cached,
    get_episode_by_season_and_number,
    get_anime_by_name,
    get_season_by_anime_and_number,
)


class ScraperHandler:
    def __init__(self, anime_url):
        self.anime_url = anime_url

    def get_anime_model_from_url(self):
        """
        Extract the anime name from the provided URL using regex.
        Assumes that the anime name is in the last part of the URL.
        """
        match = re.search(r"/([^/]+)-Dubbed-Videos", self.anime_url)  # Match the specific pattern before '-Dubbed-Videos'
        if match:
            anime_name = match.group(1).replace("-", " ").title()

        else:
            anime_name = input("please enter anime name: ")

        anime = get_anime_by_name(anime_name)
        if not anime:
            anime = add_anime(anime_name=anime_name, anime_link=self.anime_url)

        print(f"\nScraping data for anime: {anime_name}")
        return anime

    def scrap_seasons(self, anime_item):
        parent_folder = anime_item.anime_name
        response = requests.get(self.anime_url)

        # print(response.status_code)

        soup = BeautifulSoup(response.text, 'html.parser')

        result_seasons = soup.find_all('div', attrs={"class": 'Singamdasam'})
        season_items = []

        for season in result_seasons:
            # Find the single <a> tag within the current <div>
            a_tag = season.find("a")
            if not a_tag:
                continue

            season_link = "https:" + a_tag.get("href")
            # Regular expression to find 'season-' followed by a number
            match = re.search(r"season-(\d+)", season_link, re.IGNORECASE)

            if match:
                season_number = int(match.group(1))
                # print(season_number)
                full_path = os.path.join(parent_folder, str(season_number))

                season = get_season_by_anime_and_number(anime_item, season_number)
                if season not in season_items:
                    season_items.append(season)

                if not season:
                    season = add_season(
                        anime=anime_item,
                        season_number=season_number,
                        season_url=season_link,
                        season_folder_path=full_path
                    )
                    # print(season.season_url)
                    if season not in season_items:
                        season_items.append(season)

        return season_items

    def get_seasons_to_scrape(self, seasons):
        """
        Allow the user to choose which seasons to scrape.
        :param seasons: List of season objects.
        :return: List of seasons selected by the user.
        """
        while True:  # Keep asking for input until it's valid
            print("\nAvailable seasons:")
            for i, season in enumerate(seasons):
                if i < len(seasons) - 1:
                    print(f"Season {season.season_number}", end=", ")
                else:
                    print(f"Season {season.season_number}")

            # Ask user for input
            selected_seasons = input(
                "\nEnter the seasons you want to scrape (comma-separated, e.g. 1,2,3)\n"
                "'all' for all seasons\n"
                "or 'exit' to quit:"
            ).strip().lower()

            if selected_seasons == 'exit':
                print("Exiting the program.")
                exit()  # Exit if the user enters 'exit'

            if selected_seasons == 'all':
                # If the user selects 'all', return all seasons
                return [season for season in seasons]

            # Otherwise, parse the input
            selected_seasons = selected_seasons.split(',')
            valid_seasons = {season.season_number: season for season in seasons}  # Create a mapping of number to object
            seasons_to_scrape = [valid_seasons[int(s.strip())] for s in selected_seasons if
                                 int(s.strip()) in valid_seasons]

            if not seasons_to_scrape:
                print("No valid seasons selected. Please try again.")
            else:
                return seasons_to_scrape  # Return if valid seasons are selected

    def scrape_episodes_of_season(self, season_item):
        full_path = season_item.season_folder_path
        episodes = []
        try:
            # Send a request to the season page
            response = requests.get(season_item.season_url)
            response.raise_for_status()  # Ensure we got a valid response

            # Parse the page content
            soup = BeautifulSoup(response.content, "html.parser")

            # Find the pagination container
            page_tag = soup.find('ul', attrs={"class": "pagination"})

            if page_tag:
                pages = page_tag.find_all('li')

                for page in pages:
                    # Find the single <a> tag within the current <div>
                    a_tag = page.find("a")
                    if a_tag:  # Ensure <a> tag exists
                        season_page_link = season_item.season_url + a_tag.get("href")
                        # print(season_page_link)

                        # Fetch episodes from this page
                        episodes_in_page = self.find_season_episodes_from_page(
                            season_page_link=season_page_link,
                            episode_folder_path=full_path,
                            season_item=season_item,
                            soup=None
                        )
                        episodes.extend(episodes_in_page)

            else:
                # If pagination is not found, scrape the first season page directly
                print("No pagination found. Scraping episodes from the first page.")
                episodes = self.find_season_episodes_from_page(
                    season_page_link=season_item.season_url,
                    episode_folder_path=full_path,
                    season_item=season_item,
                    soup=soup
                )

        except requests.exceptions.RequestException as e:
            print(f"An error occurred while requesting the page: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

        return episodes

    def find_season_episodes_from_page(self, season_page_link, episode_folder_path, season_item, soup):
        episodes = []
        if soup is None:
            response = requests.get(season_page_link)
            soup = BeautifulSoup(response.text, 'html.parser')

        # Find all <div class="Singamdasam"> elements
        result_episodes = soup.find_all('div', attrs={"class": 'Singamdasam'})

        for episode in result_episodes:
            # Find the single <a> tag within the current <div>
            a_tag = episode.find("a")
            if a_tag:  # Ensure <a> tag exists
                episode_link = "https:" + a_tag.get("href")

                # Check for '/<number> ' pattern
                match_file_number = re.search(r"/(\d+)\s", episode_link)
                if match_file_number:
                    episode_number_from_url = match_file_number.group(1)
                    # print(episode_number_from_url)
                    # print(episode_link)
                    episode_item = get_episode_by_season_and_number(season_item, episode_number_from_url)
                    if not episode_item:
                        episode_item = self.get_episode_item(
                            episode_info_link=episode_link,
                            episode_folder_path=episode_folder_path,
                            season_item=season_item
                        )
                    if episode_item not in episodes:
                        episodes.append(episode_item)
                    continue  # Skip further checks for this link

                # Check for 'Episode-' or 'Season-' pattern
                match_episode_season = re.findall(r"(?:Episode-|Season-)(\d+)", episode_link, re.IGNORECASE)
                if match_episode_season:
                    episode_number_from_url = int(match_episode_season[1])
                    # print(episode_number_from_url)
                    print(episode_link)
                    episode_item = get_episode_by_season_and_number(season_item, episode_number_from_url)
                    print(episode_item)
                    if not episode_item:
                        episode_item = self.get_episodes_info_url(
                            episode_link=episode_link,
                            episode_folder_path=episode_folder_path,
                            season_item=season_item
                        )
                    # for episode_item in episode_items:
                    print(episode_item.episode_number)
                    if episode_item not in episodes:
                        episodes.append(episode_item)

        return episodes

    def get_episodes_info_url(self, episode_link, episode_folder_path, season_item):
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

        episode_items = list()
        # Print the extracted links
        for link in links:
            # print(f"Link: {link}")
            episode_item = self.get_episode_item(
                episode_info_link=link,
                episode_folder_path=episode_folder_path,
                season_item=season_item
            )
            episode_items.append(episode_item)

        return episode_items

    def get_episode_item(self, episode_info_link, episode_folder_path, season_item):
        # extract the episode number from the URL using a regular expression
        # print(episode_info_link)
        episode_number_from_url = int(re.search(r'(\d+)(?=\s+[A-Za-z])', episode_info_link, re.IGNORECASE).group(1))

        # check if episode exists in database
        episode = get_episode_by_season_and_number(season_item, episode_number_from_url)
        if not episode:
            response = requests.get(episode_info_link)
            soup = BeautifulSoup(response.text, 'html.parser')
            base_url = "https://eng.cartoonsarea.cc"

            # Find the information div
            info_div = soup.find('div', class_='Singamdasam text-center')
            if not info_div:
                print("No information div found.")
                return None

            # Parse episode details from the table
            details = {}
            table = info_div.find('table')
            if table:
                for row in table.find_all('tr'):
                    label = row.find('td', class_='desc_label')
                    value = row.find('td', class_='desc_value')
                    if label and value:
                        details[label.text.strip()] = value.text.strip()

            # Extract download link
            download_link_tag = table.find_next('a', class_='download-btn')
            if not download_link_tag or 'href' not in download_link_tag.attrs:
                print("No download link found.")
                return None

            full_download_url = urljoin(base_url, download_link_tag['href'])
            # print(full_download_url)
            # print(details)

            # Extract required fields
            file_name = details.get("File Name:", "Unknown")
            episode_size = details.get("File Size:", "Unknown")
            duration = details.get("Duration:", "Unknown")
            file_format = details.get("File Format:", "Unknown")
            resolution = details.get("Resolution:", "Unknown")

            # Extract episode number and name
            try:
                episode_number = int(file_name.split()[0])  # Assuming episode number is the first part
            except (ValueError, IndexError):
                episode_number = -1  # Default value for error
                print("Could not determine episode number.")

            episode_name = file_name.split(maxsplit=1)[-1].rsplit('.', 1)[0]  # Extract name without extension

            # Create the Episode instance
            episode = add_episode(
                season=season_item,
                episode_number=episode_number,
                episode_name=episode_name,
                file_name=file_name,
                episode_size=episode_size,
                duration=duration,
                file_format=file_format,
                resolution=resolution,
                episode_url=full_download_url,
                episode_folder_path=episode_folder_path,
            )
            mark_episode_as_cached(episode)
        return episode
