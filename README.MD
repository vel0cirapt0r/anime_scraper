# Anime Scraper and Downloader

This project demonstrates my ability to develop a scraper that downloads files in a structured manner while implementing caching. **It is strictly for educational purposes and should not be used to violate copyright laws.** The scraper is designed to work exclusively with the website [https://eng.cartoonsarea.cc](https://eng.cartoonsarea.cc).

## Disclaimer

**This project is for educational purposes only.**\
The creator does not encourage or endorse illegal downloading or copyright infringement. Users must ensure they have legal permission to access and download content. Any misuse of this code is the sole responsibility of the user.

---

## Features

- Scrapes anime seasons and episodes from a specified URL.
- Downloads episodes into structured folders:
  - **Anime Folder**: Created with the anime's name.
  - **Season Folders**: Subfolders for each selected season.
  - **Episode Files**: Episodes are downloaded into the corresponding season folder.
- Implements caching to avoid redundant downloads.
- User-friendly prompts for selecting anime seasons to scrape and download.

---

## Technical Highlights

- **Structured Scraping**: Dynamically parses URLs and extracts data to create a logical folder structure.
- **Database Integration**: Uses Peewee ORM to manage caching, ensuring efficient data retrieval and minimizing redundant requests.
- **Error Handling**: Robust mechanisms to handle unexpected errors and provide clear feedback to the user.
- Parallel Downloads: Optimize download speeds by implementing multi-threaded or asynchronous downloads, enabling up to 4 episodes to be downloaded concurrently for faster completion of large seasons.
- **Dynamic User Prompts**: Guides the user through URL input, season selection, and download confirmation seamlessly.

---

## Requirements

This project requires **Python 3.12.2** or above.

### Dependencies

Install the required dependencies listed in `requirements.txt`:

```bash
pip install -r requirements.txt
```

Before installing dependencies, create a virtual environment:

- **macOS/Linux**:
  ```bash
  virtualenv -p python3.12 venv_scraper
  source venv_scraper/bin/activate
  ```
- **Windows**:
  ```cmd
  python -m venv venv_scraper
  venv_scraper\Scripts\activate
  ```

---

## Usage

1. Clone the repository:

```bash
git clone https://github.com/vel0cirapt0r/anime_scraper
cd anime_scraper
```

2. Activate the virtual environment (see above).

3. Run the scraper:

   ```bash
   python main.py
   ```

4. Follow the prompts:

   - Enter the URL of the anime (default: `https://eng.cartoonsarea.cc/English-Dubbed-Series/O-Dubbed-Series/One-Piece-Dubbed-Videos/#gsc.tab=0`).
     - **Note**: The user must find the anime's URL directly from the website. The default URL is pre-set for *One Piece* as an example.
   - Select the seasons you wish to scrape (e.g., `1,2,3` or `all`).
   - Confirm the episodes to download.

---

## Future Enhancements

- **GUI**: Add a graphical user interface for a more intuitive user experience.
- **Metadata Extraction**: Automatically save metadata (e.g., episode descriptions, air dates) alongside downloaded episodes.

---

## Contribution Guide

Contributions are welcome! To contribute:

1. Fork the repository.
2. Create a feature branch:
   ```bash
   git checkout -b feature-name
   ```
3. Commit your changes:
   ```bash
   git commit -m "Description of changes"
   ```
4. Push to your branch:
   ```bash
   git push origin feature-name
   ```
5. Open a pull request.

---

## License

This project is licensed under the MIT License. See the LICENSE file for more details.

