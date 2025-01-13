import scraper_handler
from scraper_handler import ScraperHandler


if __name__ == "__main__":
    anime_url = 'https://eng.cartoonsarea.cc/English-Dubbed-Series/O-Dubbed-Series/One-Piece-Dubbed-Videos/#gsc.tab=0'
    scraper = ScraperHandler(anime_url)
    season = scraper.scrap_seasons()
    episodes = list()
    for season in season:
        # if season.season_number == 9:
        #     print("#-" * 50)
        #     print(season.season_number)
        #     print("^" * 50)
        #     pass
        # else:
        episode = scraper.scrape_episodes_of_season(season_item=season)
        # episodes.sort()
        # print(len(episode))
        for episode in episode:
            if episode not in episodes:
                print(f"season: {season}, episode: {episode}")
                episodes.append(episode)

    print(len(episodes))
