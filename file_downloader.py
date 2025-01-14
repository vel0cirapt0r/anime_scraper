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

    def download_file(self, url, target_path):
        """
        Download a single file with support for resuming partial downloads.
        :param url: The file URL.
        :param target_path: The path to save the file.
        """
        try:
            os.makedirs(os.path.dirname(target_path), exist_ok=True)

            # Get the total size of the file from the server
            total_size = self.get_file_size(url)

            # Determine the starting point of the download
            downloaded_size = os.path.getsize(target_path) if os.path.exists(target_path) else 0

            # If the file is already fully downloaded, skip it
            if total_size and downloaded_size >= total_size:
                print(f"Skipping download, file already complete: {target_path}")
                return True

            headers = {"Range": f"bytes={downloaded_size}-"} if downloaded_size > 0 else {}
            with requests.get(url, stream=True, headers=headers, timeout=self.timeout) as response:
                response.raise_for_status()
                mode = "ab" if downloaded_size > 0 else "wb"  # Append for partial downloads
                with open(target_path, mode) as file, tqdm(
                    desc=os.path.basename(target_path),
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
            print(f"Failed to download {url}. Error: {e}")
            return False  # Failure

    def download_files(self, url_list, target_dir):
        """
        Download multiple files with support for parallelism.
        :param url_list: List of file URLs.
        :param target_dir: Directory to save the files.
        """
        def download_task(url):
            filename = os.path.basename(url)
            target_path = os.path.join(target_dir, filename)
            return self.download_file(url, target_path)

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            results = list(executor.map(download_task, url_list))

        return results


# Example usage
if __name__ == "__main__":
    downloader = FileDownloader()
    urls = [
        "https://eng.cartoonsarea.cc/USER-DATA/Cartoonsarea/English/O/One Piece/Season 2/Episode 74//74 The Devilish Candle!.mp4",
        "https://eng.cartoonsarea.cc/USER-DATA/Cartoonsarea/English/O/One Piece/Season 2/Episode 75//75 A Hex on Luffy!.mp4",
        "https://eng.cartoonsarea.cc/USER-DATA/Cartoonsarea/English/O/One Piece/Season 2/Episode 76//76 Time to Fight Back!.mp4",
    ]
    target_directory = "downloads"
    downloader.download_files(urls, target_directory)
