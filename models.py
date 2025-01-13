class Season:
    def __init__(self, season_number, season_url, season_folder_path):
        self.season_number = season_number
        self.season_url = season_url
        self.season_folder_path = season_folder_path

    def __str__(self):
        return f"Season {self.season_number}"


class Episode:
    def __init__(self, episode_number, episode_name, episode_url, episode_folder_path, season_number):
        self.episode_number = episode_number
        self.episode_name = episode_name
        self.episode_url = episode_url
        self.episode_folder_path = episode_folder_path
        self.season_number = season_number  # Foreign reference to a season

    def __str__(self):
        return f"Episode {self.episode_number}: {self.episode_name} (Season {self.season_number})"
