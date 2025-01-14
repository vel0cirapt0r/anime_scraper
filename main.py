import re
from scraper_handler import ScraperHandler
from file_downloader import FileDownloader


def get_anime_name_from_url(url):
    """
    Extract the anime name from the provided URL using regex.
    Assumes that the anime name is in the last part of the URL.
    """
    match = re.search(r"/([^/]+)-Dubbed-Videos", url)  # Match the specific pattern before '-Dubbed-Videos'
    if match:
        return match.group(1).replace("-", " ").title()
    return "Unknown Anime"


def get_seasons_to_scrape(seasons):
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
            "\nEnter the seasons you want to scrape (comma-separated, e.g. 1,2,3), 'all' for all seasons"
            ", or 'exit' to quit:"
        ).strip().lower()

        if selected_seasons == 'exit':
            print("Exiting the program.")
            exit()  # Exit if the user enters 'exit'

        if selected_seasons == 'all':
            # If the user selects 'all', return all seasons
            return [season.season_number for season in seasons]

        # Otherwise, parse the input
        selected_seasons = selected_seasons.split(',')
        valid_seasons = [season.season_number for season in seasons]
        seasons_to_scrape = [int(s.strip()) for s in selected_seasons if int(s.strip()) in valid_seasons]

        if not seasons_to_scrape:
            print("No valid seasons selected. Please try again.")
        else:
            return seasons_to_scrape  # Return if valid seasons are selected


def get_anime_url():
    """
    Get the anime URL from the user.
    If the user doesn't provide an input, the default URL is used.
    """
    default_url = 'https://eng.cartoonsarea.cc/English-Dubbed-Series/O-Dubbed-Series/One-Piece-Dubbed-Videos/#gsc.tab=0'

    while True:
        anime_url = input(f"Enter the URL of the anime (default: {default_url}): ").strip()
        if anime_url == "":
            anime_url = default_url
            break
        elif re.match(r"https?://", anime_url):  # Simple validation for URL format
            break
        else:
            print("Invalid URL format. Please enter a valid URL or leave blank for the default URL.")

    return anime_url


def get_download_confirmation():
    """
    Ask the user for download confirmation.
    Repeats the prompt until the user provides a valid response.
    """
    while True:
        download_confirm = input("\nDo you want to download the episodes? (yes/no): ").strip().lower()
        if download_confirm in ["yes", "y"]:
            return True
        elif download_confirm in ["no", "n"]:
            return False
        else:
            print("Invalid input. Please enter 'yes' or 'no'.")


if __name__ == "__main__":
    # Get the anime URL from the user
    anime_url = get_anime_url()

    # Extract anime name from URL
    anime_name = get_anime_name_from_url(anime_url)
    print(f"\nScraping data for anime: {anime_name}")

    # Initialize the scraper
    scraper = ScraperHandler(anime_url)

    # Fetch seasons
    seasons = scraper.scrap_seasons()

    print(f"\n{anime_name} has {len(seasons)} seasons available.")

    # Ask the user which seasons to scrape
    seasons_to_scrape = get_seasons_to_scrape(seasons)

    all_episodes = list()

    # Iterate over each selected season
    for season in seasons:
        if season.season_number not in seasons_to_scrape:
            continue  # Skip seasons not selected by the user

        # Fetch episodes for the selected season
        episodes_in_season = scraper.scrape_episodes_of_season(season_item=season)

        # Sort episodes by their number
        sorted_episodes = sorted(episodes_in_season, key=lambda episode: episode.episode_number)

        # Print details for the selected season
        print(f"\nSeason {season.season_number} has {len(sorted_episodes)} episodes.")

        # Add unique episodes to the main list
        for episode in sorted_episodes:
            if episode not in all_episodes:
                print(episode)
                # print(episode.episode_url)
                all_episodes.append(episode)

    # Print the total number of episodes collected
    print(f"\n{anime_name} has a total of {len(all_episodes)} episodes.")

    # Ask the user if they want to start downloading the episodes
    if get_download_confirmation():
        downloader = FileDownloader()
        download_results = downloader.download_episodes(all_episodes)
        print(f"Download completed for {sum(download_results)} episodes.")
    else:
        print("Download skipped.")
