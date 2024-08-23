import os
import subprocess
import shutil

from .writeMP3 import write_mp3_with_metadata

album_folder_path = os.path.join(os.path.dirname(__file__), "..", "album")


async def delete_old():
    if not os.path.exists(album_folder_path):
        os.makedirs(album_folder_path)
        return

    for file_name in os.listdir(album_folder_path):
        file_path = os.path.join(album_folder_path, file_name)
        try:
            os.remove(file_path)
            print(f"Deleted file: {file_path}")
        except Exception as e:
            print(f"Error deleting file: {file_path} - {e}")


async def download_tracks(soup, specified_link):
    # Grab the name of the album to name the directory
    album_title = soup.select_one(".album_title").get_text().split('\n')[0].strip()
    global album_folder_path
    album_folder_path = album_title
    await delete_old()

    specified_link = specified_link.replace("https://", "")

    link_parsed = specified_link.split("/")

    yt_dlp_path = shutil.which("yt-dlp")
    if link_parsed[-2] == "sets":
        subprocess.call([yt_dlp_path, "-x", "--embed-metadata", "--audio-format", "mp3", "--output", f"{album_folder_path}/%(playlist_index)d.%(ext)s", specified_link])
    else:
        subprocess.call([yt_dlp_path, "-x", "--embed-metadata", "--audio-format", "mp3", "--output", f"{album_folder_path}/0.%(ext)s", specified_link])

async def handle_soundcloud_link(soup, specified_link):
    await download_tracks(soup, specified_link)
    await write_mp3_with_metadata(soup)
