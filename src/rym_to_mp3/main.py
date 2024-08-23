import argparse

from .splitHandler import handle_split_request
from .YouTubeHandler import handle_youtube_link
import asyncio
from .SoundCloudHandler import handle_soundcloud_link
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="The URL to scrape, or the file path when splitting with -x")
    parser.add_argument("-u", "--YouTubeLink", help="Specify a specific YouTube link")
    parser.add_argument("-t", "--timestamps", help="Specify your own timestamps to use for YouTube parsing")
    parser.add_argument("-s", "--SoundCloudLink", help="Specify a specific SoundCloud link")
    parser.add_argument("-y", "--preferYouTube", action="store_true", help="Prefer YouTube")
    parser.add_argument("-i", "--ignore", action="store_true", help="Ignore discrepancy between album length and YouTube video length")
    parser.add_argument("-x", "--split", action="store_true", help="Split audio into individual tracks")
    args = parser.parse_args()

    if args.split:
        asyncio.run(handle_split_request(args.url, args.timestamps))
        return
    
    try:
        # Set up Chrome options
        chrome_options = webdriver.ChromeOptions()

        # Initialize the Chrome driver
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

        # Go to the URL
        driver.get(args.url)
        
        WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div.ui_media_links_container'))
        )

        data = driver.page_source
        driver.quit()
        soup = BeautifulSoup(data, 'html.parser')
    except Exception as e:
        print("Something went wrong trying to scrape RYM. This can happen fairly frequently. Try again!")
    finally:
        driver.quit()

    try:
        YouTubeLink = args.YouTubeLink if args.YouTubeLink else soup.find('a', class_='ui_media_link_btn_youtube').get('href')
    except Exception as e:
        print("No valid YouTube link found!")
        YouTubeLink = None
    try:
        SoundCloudLink = args.SoundCloudLink if args.SoundCloudLink else soup.find('a', class_='ui_media_link_btn_soundcloud').get('href')
    except Exception as e:
        print("No valid SoundCloud link found!")
        SoundCloudLink = None

    print(f"YouTube Link: {YouTubeLink}")
    print(f"SoundCloud Link: {SoundCloudLink}")
    if args.preferYouTube:
        if YouTubeLink:
            print("Handling YouTube link...")
            asyncio.run(handle_youtube_link(soup, YouTubeLink, args.ignore, args.timestamps))
        elif SoundCloudLink:
            print("Handling SoundCloud link...")
            asyncio.run(handle_soundcloud_link(soup, SoundCloudLink))
        else:
            print("No YouTube or SoundCloud link found.")
    else:
        if SoundCloudLink:
            print("Handling SoundCloud link...")
            asyncio.run(handle_soundcloud_link(soup, SoundCloudLink))
        elif YouTubeLink:
            print("Handling YouTube link...")
            asyncio.run(handle_youtube_link(soup, YouTubeLink, args.ignore, args.timestamps))
        else:
            print("No YouTube or SoundCloud link found.")

if __name__ == "__main__":
    main()

