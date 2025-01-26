import os
import requests
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm


class FileDownloader:
    def __init__(self, retries=3, timeout=10, max_workers=4):
        """
        Initialize the downloader.
        :param retries: Number of retry attempts for failed downloads.
        :param timeout: Timeout for each request in seconds.
        :param max_workers: Maximum number of parallel downloads.
        """
        self.retries = retries
        self.timeout = timeout
        self.max_workers = max_workers

    def get_download_confirmation():
        """
        Ask the user for download confirmation.
        Repeats the prompt until the user provides a valid response.
        """
        while True:
            download_confirm = input("\nDo you want to download the episodes? (yes/no): ").strip().lower() or "yes"
            if download_confirm in ["yes", "y"]:
                return True
            elif download_confirm in ["no", "n"]:
                return False
            else:
                print("Invalid input. Please enter 'yes' or 'no'.")

    def get_file_size(self, url):
        """
        Get the size of the file from the server using a HEAD request.
        :param url: The file URL.
        :return: File size in bytes or None if not available.
        """
        try:
            response = requests.head(url, timeout=self.timeout)
            response.raise_for_status()
            return int(response.headers.get("content-length", 0))
        except Exception as e:
            print(f"Failed to retrieve file size for {url}. Error: {e}")
            return None

    def create_folder(self, folder_path):
        """
        Create the folder if it doesn't exist.
        :param folder_path: Path where the folder should be created.
        """
        try:
            os.makedirs(folder_path, exist_ok=True)
            print(f"Folder created: {folder_path}")
        except Exception as e:
            print(f"Error creating folder {folder_path}: {e}")

    def download_file(self, episode):
        """
        Download a single episode file with support for resuming partial downloads.
        :param episode: Episode object containing episode details.
        """
        try:
            # Create folder if it doesn't exist
            self.create_folder(episode.episode_folder_path)

            # Construct the target path for saving the episode file
            episode_file_name_with_space = f"{episode.episode_number}_{episode.episode_name}.mp4"
            episode_file_name = episode_file_name_with_space.replace(" ", "_")
            target_path = os.path.join(episode.episode_folder_path, episode_file_name)

            # Get the total size of the file from the server
            total_size = self.get_file_size(episode.episode_url)

            # Determine the starting point of the download
            downloaded_size = os.path.getsize(target_path) if os.path.exists(target_path) else 0

            # If the file is already fully downloaded, skip it
            if total_size and downloaded_size >= total_size:
                print(f"Skipping download, file already complete: {target_path}")
                return True

            headers = {"Range": f"bytes={downloaded_size}-"} if downloaded_size > 0 else {}
            with requests.get(episode.episode_url, stream=True, headers=headers, timeout=self.timeout) as response:
                response.raise_for_status()
                mode = "ab" if downloaded_size > 0 else "wb"  # Append for partial downloads
                with open(target_path, mode) as file, tqdm(
                        desc=episode.episode_name,
                        total=total_size,
                        initial=downloaded_size,
                        unit="B",
                        unit_scale=True,
                        unit_divisor=1024,
                ) as bar:
                    for chunk in response.iter_content(chunk_size=8192):
                        file.write(chunk)
                        bar.update(len(chunk))

            return True  # Success
        except Exception as e:
            print(f"Failed to download {episode.episode_name}. Error: {e}")
            return False  # Failure

    def download_episodes(self, episodes):
        """
        Download multiple episodes with support for parallelism.
        :param episodes: List of Episode objects to download.
        """
        def download_task(episode):
            return self.download_file(episode)

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            results = list(executor.map(download_task, episodes))

        return results
