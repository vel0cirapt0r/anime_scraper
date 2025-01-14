from scraper_handler import ScraperHandler

if __name__ == "__main__":
    # URL for the anime to scrape
    anime_url = 'https://eng.cartoonsarea.cc/English-Dubbed-Series/O-Dubbed-Series/One-Piece-Dubbed-Videos/#gsc.tab=0'

    # Initialize the scraper
    scraper = ScraperHandler(anime_url)

    # Fetch seasons
    seasons = scraper.scrap_seasons()
    all_episodes = list()

    # Iterate over each season
    for season in seasons:
        # if season.season_number != 2:
        #     # Skip other seasons
        #     pass
        # else:
        # Fetch episodes for the selected season
        episodes_in_season = scraper.scrape_episodes_of_season(season_item=season)

        # Sort episodes by their number
        sorted_episodes = sorted(episodes_in_season, key=lambda episode: episode.episode_number)

        # Print details for the selected season
        print(f"Season {season.season_number} has {len(sorted_episodes)} episodes.")

        # Add unique episodes to the main list
        for episode in sorted_episodes:
            if episode not in all_episodes:
                print(episode)
                print(episode.episode_url)
                all_episodes.append(episode)

    # Print the total number of episodes collected
    print(f"This anime has a total of {len(all_episodes)} episodes.")
