import re

from db_manager import connect_db, create_tables, close_db
from scraper_handler import ScraperHandler
from file_downloader import FileDownloader


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


if __name__ == "__main__":

    connect_db()

    # Create tables if they don't exist
    create_tables()

    # Get the anime URL from the user
    anime_url = get_anime_url()

    # Initialize the scraper
    scraper = ScraperHandler(anime_url)

    # Extract anime name from URL
    try:
        anime_model = scraper.get_anime_model_from_url()
    except Exception as e:
        print(f"Error occurred while getting anime model: {e}")
        exit(1)  # Exit the program if an error occurs

    # Fetch seasons
    try:
        seasons = scraper.scrap_seasons(anime_item=anime_model)
    except Exception as e:
        print(f"Error occurred while scraping seasons: {e}")
        exit(1)

    print(f"\n{anime_model.anime_name} has {len(seasons)} seasons available.")

    # Ask the user which seasons to scrape
    seasons_to_scrape = scraper.get_seasons_to_scrape(seasons)

    all_episodes = list()

    # Iterate over each selected season
    for season in seasons_to_scrape:

        # Fetch episodes for the selected season
        episodes_in_season = scraper.scrape_episodes_of_season(season_item=season)
        unique_episodes_in_season = list()

        # Add unique episodes to the main list
        for episode in episodes_in_season:
            # print(episode)
            if episode is not None:
                # print(episode.episode_url)
                print(f"\nEpisode number: {episode.episode_number}\nEpisode title: {episode.episode_name}")
                if episode not in all_episodes:

                    # print(episode.episode_url)
                    unique_episodes_in_season.append(episode)

        # Sort episodes by their number
        sorted_episodes = sorted(unique_episodes_in_season, key=lambda episode: episode.episode_number)

        for episode in sorted_episodes:
            all_episodes.append(episode)

        # Print details for the selected season
        print(f"\nSeason {season.season_number} has {len(sorted_episodes)} episodes.")

    # Print the total number of episodes collected
    print(f"\n{anime_model.anime_name} has a total of {len(all_episodes)} episodes.")

    # Ask the user if they want to start downloading the episodes
    if FileDownloader.get_download_confirmation():
        downloader = FileDownloader()
        download_results = downloader.download_episodes(all_episodes)
        print(f"Download completed for {sum(download_results)} episodes.")
    else:
        print("Download skipped.")

    close_db()
