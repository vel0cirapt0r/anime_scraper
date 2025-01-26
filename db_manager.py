import peewee
from models import Anime, Season, Episode

# Import DoesNotExist exception from peewee
from peewee import DoesNotExist

# Connect to the SQLite database
db = peewee.SqliteDatabase('anime_database.db')


def connect_db():
    """Establish connection to the SQLite database."""
    db.connect()


def close_db():
    """Close the database connection."""
    db.close()


def create_tables():
    """Create all the tables based on defined models."""
    with db:
        db.create_tables([Anime, Season, Episode])


def add_anime(anime_name, anime_link):
    """Add a new anime to the database."""
    anime, created = Anime.get_or_create(
        anime_name=anime_name,
        anime_link=anime_link
    )
    if created:
        print(f"Anime '{anime_name}' added to the database.")
    else:
        print(f"Anime '{anime_name}' already exists in the database.")
    return anime


def add_season(anime, season_number, season_url, season_folder_path):
    """Add a new season for an anime to the database."""
    season, created = Season.get_or_create(
        anime=anime,
        season_number=season_number,
        season_url=season_url,
        season_folder_path=season_folder_path
    )
    if created:
        print(f"Season {season_number} added for anime '{anime.anime_name}'.")
    else:
        print(f"Season {season_number} already exists for anime '{anime.anime_name}'.")
    return season


def add_episode(season, episode_number, episode_name=None, file_name=None, episode_size=None,
                duration=None, file_format=None, resolution=None, episode_url=None, episode_folder_path=None):
    """Add a new episode to a specific season."""
    episode, created = Episode.get_or_create(
        season=season,
        episode_number=episode_number,
        episode_name=episode_name,
        file_name=file_name,
        episode_size=episode_size,
        duration=duration,
        file_format=file_format,
        resolution=resolution,
        episode_url=episode_url,
        episode_folder_path=episode_folder_path
    )
    if created:
        print(f"Episode {episode_number} added to season {season.season_number} of anime '{season.anime.anime_name}'.")
    else:
        print(
            f"Episode {episode_number} already exists in season {season.season_number} of anime '{season.anime.anime_name}'.")
    return episode


def update_episode(episode, **kwargs):
    """Update an episode's details."""
    for field, value in kwargs.items():
        setattr(episode, field, value)
    episode.save()
    print(f"Episode {episode.episode_number} updated successfully.")


def mark_episode_as_cached(episode):
    """Mark an episode as cached."""
    episode.is_cached = True
    episode.save()
    print(f"Episode {episode.episode_number} marked as cached.")


def get_anime_by_name(anime_name):
    """Retrieve an anime by its name."""
    try:
        anime = Anime.get(Anime.anime_name == anime_name)
        return anime
    except DoesNotExist:
        print(f"Anime '{anime_name}' not found.")
        return None


def get_season_by_anime_and_number(anime, season_number):
    """Retrieve a season by anime and season number."""
    try:
        season = Season.get(Season.anime == anime, Season.season_number == season_number)
        return season
    except DoesNotExist:
        print(f"Season {season_number} not found for anime '{anime.anime_name}'.")
        return None


def get_episode_by_season_and_number(season, episode_number):
    """Retrieve an episode by season and episode number."""
    try:
        episode = Episode.get(Episode.season == season, Episode.episode_number == episode_number)
        return episode
    except DoesNotExist:
        print(f"Episode {episode_number} not found for season {season.season_number}.")
        return None


if __name__ == "__main__":
    # Example Usage:
    connect_db()

    # Create tables if they don't exist
    create_tables()

    # Example of adding data
    anime = add_anime('Naruto', 'https://naruto.com')
    season = add_season(anime, 1, 'https://naruto.com/season1', '/path/to/season1')
    episode = add_episode(season, 1, 'Naruto Episode 1', 'naruto_episode_1.mp4', '500MB', '22m', 'mp4', '1080p',
                          'https://naruto.com/episode1', '/path/to/episode1')

    # Mark episode as cached
    mark_episode_as_cached(episode)

    # Example of updating an episode
    update_episode(episode, episode_name="Naruto Episode 1 Updated")

    # Retrieve and print data
    anime = get_anime_by_name('Naruto')
    if anime:
        print(f"Anime: {anime.anime_name}, Link: {anime.anime_link}")

    season = get_season_by_anime_and_number(anime, 1)
    if season:
        print(f"Season: {season.season_number}, URL: {season.season_url}")

    episode = get_episode_by_season_and_number(season, 1)
    if episode:
        print(f"Episode: {episode.episode_number}, Name: {episode.episode_name}")

    close_db()
