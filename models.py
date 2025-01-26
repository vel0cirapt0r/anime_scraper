from peewee import Model, CharField, IntegerField, DateTimeField, BooleanField, ForeignKeyField
from datetime import datetime
import peewee


# Base Model for Peewee ORM
class BaseModel(Model):
    last_scraped = DateTimeField(default=datetime.now)  # Timestamp for when it was last scraped
    updated_at = DateTimeField(default=datetime.now)  # Timestamp for last update to the data
    is_cached = BooleanField(default=False)  # Flag to track whether the data is cached

    class Meta:
        database = peewee.SqliteDatabase('anime_database.db')


class Anime(BaseModel):
    anime_name = CharField(unique=True)
    anime_link = CharField(unique=True)

    def __str__(self):
        return self.anime_name


class Season(BaseModel):
    anime = ForeignKeyField(Anime, backref='seasons')  # ForeignKey to Anime model
    season_number = IntegerField()
    season_url = CharField()
    season_folder_path = CharField()

    class Meta:
        indexes = (
            (('anime', 'season_number'), True),  # Unique per anime
        )

    def __str__(self):
        return f"Season {self.season_number} (Anime {self.anime.anime_name})"


class Episode(BaseModel):
    season = ForeignKeyField(Season, backref='episodes')  # ForeignKey to Season model
    episode_number = IntegerField()
    episode_name = CharField(null=True)
    file_name = CharField(null=True)
    episode_size = CharField(null=True)
    duration = CharField(null=True)
    file_format = CharField(null=True)
    resolution = CharField(null=True)
    episode_url = CharField(null=True)
    episode_folder_path = CharField(null=True)
    retry_count = IntegerField(default=0)  # Tracks failed scraping attempts

    class Meta:
        indexes = (
            (('season', 'episode_number'), True),  # Unique per season
        )

    def __str__(self):
        return f"Episode {self.episode_number}: {self.episode_name} (Season {self.season.season_number}) (Anime {self.season.anime.anime_name})"
