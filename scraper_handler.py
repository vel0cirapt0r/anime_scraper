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
        """
        Initialize the ScraperHandler with the provided anime URL.

        :param anime_url: The URL of the anime to scrape.
        """
        self.anime_url = anime_url

    def get_anime_model_from_url(self):
        """
        Extract the anime name from the given URL or prompt the user to input it if not found.
        Check the database for an existing anime entry, and create one if it doesn't exist.

        :return: The Anime model instance for the scraped anime.
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
        """
        Scrape the seasons for the given anime from the website and save them to the database.
        If a season already exists, it will not be added again.

        :param anime_item: The Anime model instance for which seasons are being scraped.
        :return: A list of Season model instances for the scraped seasons.
        """
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
        Prompt the user to select which seasons to scrape from a list of available seasons.

        :param seasons: A list of Season model instances.
        :return: A list of Season model instances selected by the user for scraping.
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
        """
        Scrape all episodes for a given season. If pagination exists on the season page,
        scrape episodes across all pages. Add episodes to the database or retrieve them
        if they already exist.

        :param season_item: The Season model instance for which episodes are being scraped.
        :return: A list of Episode model instances for the scraped episodes.
        """
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
                    # print(a_tag)
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
        """
        Scrape episodes from a single page of a season.
        Determine whether to use `get_episode_item` or `get_episodes_info_url` based on the
        URL structure.

        :param season_page_link: The URL of the season page to scrape.
        :param episode_folder_path: The folder path where episodes are saved locally.
        :param season_item: The Season model instance to which the episodes belong.
        :param soup: (Optional) BeautifulSoup object for the parsed HTML of the page.
        :return: A list of Episode model instances scraped from the page.
        """
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

                # Extract episode number and decide function
                episode_number, function_identifier = self.extract_episode_number(episode_link)
                if not episode_number and episode_link != "https://eng.cartoonsarea.cc/":
                    print(f"couldn't find episode number from {episode_link}")
                    continue  # Skip if no valid episode number is found

                # Check if the episode already exists in the database
                episode_item = get_episode_by_season_and_number(season_item, episode_number)
                if not episode_item:
                    # Use the appropriate function based on the identifier
                    if function_identifier == 1:
                        episode_item = self.get_episode_item(
                            episode_info_link=episode_link,
                            episode_folder_path=episode_folder_path,
                            season_item=season_item
                        )
                    elif function_identifier == 2:
                        episode_item = self.get_episodes_info_url(
                            episode_link=episode_link,
                            episode_folder_path=episode_folder_path,
                            season_item=season_item
                        )

                # Add the episode to the list if it's unique
                if episode_item and episode_item not in episodes:
                    episodes.append(episode_item)

        return episodes

    def extract_episode_number(self, url):
        """
        Extract the episode number from the given URL and indicate which function to use.
        :param url: The URL containing the episode information.
        :return: A tuple (episode_number, identifier) where identifier is 1 or 2.
        """
        # First pattern: Match '/123 ' (number followed by a space)
        match_file_number = re.search(r"/(\d+)\s", url)
        if match_file_number:
            return int(match_file_number.group(1)), 1

        # Second pattern: Match 'Episode-123' or 'Season-123'
        match_episode_season = re.findall(r"(?:Episode-|Season-)(\d+)", url, re.IGNORECASE)
        if match_episode_season and len(match_episode_season) > 1:  # Ensure there are enough matches
            return int(match_episode_season[1]), 2

        # If no matches are found
        if url != "https://eng.cartoonsarea.cc/":
            print(f"Unable to extract episode number from URL: {url}")
        return None, None

    def get_episodes_info_url(self, episode_link, episode_folder_path, season_item):
        """
        Scrape detailed episode information from a given episode link. Extract
        metadata such as episode name, size, format, resolution, and download URL.
        Save the episode to the database.

        :param episode_link: The URL of the episode page to scrape.
        :param episode_folder_path: The folder path where the episode will be saved.
        :param season_item: The Season model instance to which the episode belongs.
        :return: A list of Episode model instances with detailed metadata.
        """
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
        """
        Scrape basic episode information from a given link. Extract metadata
        such as the episode number and name. Save the episode to the database.

        :param episode_info_link: The URL containing basic episode information.
        :param episode_folder_path: The folder path where the episode will be saved.
        :param season_item: The Season model instance to which the episode belongs.
        :return: An Episode model instance with basic metadata or None if scraping fails.
        """
        response = requests.get(episode_info_link)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract details using the modular function
        details = self.extract_episode_details(soup)
        if not details or not details.get("episode_url"):
            print(f"Failed to scrape details for episode at {episode_info_link}. Skipping.")
            return None

        # Add the episode to the database
        episode = add_episode(
            season=season_item,
            episode_number=details["episode_number"],
            episode_name=details["episode_name"],
            file_name=details["file_name"],
            episode_size=details["episode_size"],
            duration=details["duration"],
            file_format=details["file_format"],
            resolution=details["resolution"],
            episode_url=details["episode_url"],
            episode_folder_path=episode_folder_path,
        )
        mark_episode_as_cached(episode)
        return episode

    def extract_episode_details(self, soup):
        """
        Extract detailed metadata for an episode from a BeautifulSoup object.

        :param soup: BeautifulSoup object of the episode page.
        :return: A dictionary containing episode metadata.
        """
        details = {}

        # Locate the information table
        info_div = soup.find('div', class_='Singamdasam text-center')
        if not info_div:
            print("No information div found.")
            return None

        # Parse the details table
        table = info_div.find('table')
        if table:
            for row in table.find_all('tr'):
                label = row.find('td', class_='desc_label')
                value = row.find('td', class_='desc_value')
                if label and value:
                    details[label.text.strip()] = value.text.strip()

        # Extract the download link
        download_link_tag = table.find_next('a', class_='download-btn') if table else None
        if download_link_tag and 'href' in download_link_tag.attrs:
            details['episode_url'] = urljoin("https://eng.cartoonsarea.cc", download_link_tag['href'])
        else:
            print("No download link found.")
            details['episode_url'] = None

        # Extract file name and infer other details
        file_name = details.get("File Name:", "Unknown")
        details["file_name"] = file_name
        details["episode_size"] = details.get("File Size:", "Unknown")
        details["duration"] = details.get("Duration:", "Unknown")
        details["file_format"] = details.get("File Format:", "Unknown")
        details["resolution"] = details.get("Resolution:", "Unknown")

        # Extract episode number and name
        try:
            details["episode_number"] = int(file_name.split()[0])  # Assuming episode number is the first part
        except (ValueError, IndexError):
            details["episode_number"] = -1
            print("Could not determine episode number.")

        details["episode_name"] = file_name.split(maxsplit=1)[-1].rsplit('.', 1)[0] if " " in file_name else "Unknown"
        return details
