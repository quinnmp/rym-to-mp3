import os
import re
import yt_dlp
import ffmpeg
import asyncio

from .writeMP3 import write_mp3_with_metadata
from .splitMP3 import split_mp3

album_folder_path = os.path.join(os.path.dirname(__file__), "..", "album")
track_lengths = []
ignore_discrepancy = False
custom_timestamps = ""
download_successful = False

async def get_video_length(video_url):
    try:
        info = await asyncio.to_thread(yt_dlp.YoutubeDL().extract_info, video_url, download=False)
        video_length_in_seconds = info.get("duration", 0) - 1
        return video_length_in_seconds
    except Exception as e:
        print(f"Error getting video length: {e}")
        raise e


def get_track_lengths(soup):
    # Grab the name of the album to name the directory
    album_title = soup.select_one(".album_title").get_text().split('\n')[0].strip()
    global album_folder_path
    album_folder_path = album_title

    # Find the <ul> element with id "tracks"
    ul_element = soup.select_one("#tracks")

    if ul_element:
        # Find all <li> elements inside the <ul>
        # The last one is the total length, which we don't care about, so we remove that one
        li_elements = ul_element.select("li.track")[:-1]

        # print(f"select_one span {int(li.select_one('span.tracklist_duration').get('data-inseconds', 0))}")
        # Extract text content from the final <span> element in each <li>
        span_text_array = [
            int(li.select_one('span.tracklist_duration').get('data-inseconds', 0))
            for li in li_elements
        ]

        cumulative_timestamp_array = []
        if custom_timestamps:
            cumulative_timestamp_array = handle_custom_timestamps(custom_timestamps)
            if len(cumulative_timestamp_array) - 1 != len(span_text_array):
                raise ValueError(
                    f"Got {len(cumulative_timestamp_array) - 1} custom timestamps, but there should be {len(span_text_array)}"
                )
        else:
            cumulative_timestamp_array = [0]
            for duration in span_text_array:
                cumulative_timestamp_array.append(
                    cumulative_timestamp_array[-1] + duration
                )

        return cumulative_timestamp_array
    else:
        raise ValueError('No <ul> element with id "tracks" found.')


async def download_tracks(soup, specified_link):
    global track_lengths, download_successful
    track_lengths = get_track_lengths(soup)

    video_url = specified_link if specified_link else soup.find('a', class_='ui_media_link_btn_youtube').get('href')
    try:
        duration = await get_video_length(video_url)
        if not ignore_discrepancy and abs(
            duration - track_lengths[-1]
        ) > 2:
            raise ValueError(
                "Album duration and YouTube video length differ by more than 2 seconds, indicating some poor cropping. Run again with -i to ignore this error."
            )
        print("Downloading audio...")
        options = {
            "format": "bestaudio/best",
            "outtmpl": "fullAudio.%(ext)s",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
        }
        with yt_dlp.YoutubeDL(options) as ydl:
            ydl.download([video_url])

        await delete_album_files()
        download_successful = True
    except Exception as e:
        print(f"Error downloading tracks: {e}")


async def delete_album_files():
    if not os.path.exists(album_folder_path):
        os.makedirs(album_folder_path)
        return

    for file_name in os.listdir(album_folder_path):
        file_path = os.path.join(album_folder_path, file_name)
        try:
            os.unlink(file_path)
            print(f"Deleted file: {file_path}")
        except Exception as e:
            print(f"Error deleting file: {file_path} - {e}")


async def process_audio():
    for index, length in enumerate(track_lengths[:-1]):
        output_file = os.path.join(album_folder_path, f"{index}.mp3")
        open(output_file, "w").close()  # Create an empty file

        print(f"File {index}.mp3 has been created successfully.")

        try:
            start_time = track_lengths[index]
            end_time = track_lengths[index + 1]

            stream = ffmpeg.input("fullAudio.mp3", ss=start_time)
            if end_time != float("inf"):
                stream = ffmpeg.output(
                    stream, output_file, acodec="libmp3lame", to=end_time - start_time
                )
            else:
                stream = ffmpeg.output(stream, output_file, acodec="libmp3lame")

            ffmpeg.run(stream, overwrite_output=True)
            print(f"Audio cropped for track {index}")
        except Exception as e:
            print(f"Error cropping audio: {e}")


def handle_custom_timestamps(custom_timestamps):
    pattern = r"\b(?:\d{1,2}:)?\d{1,2}:\d{2}\b"
    timestamps = re.findall(pattern, custom_timestamps)
    print(f"Custom timestamps: {timestamps}")

    durations_in_seconds = []
    for timestamp in timestamps:
        timestamp_split = [int(x) for x in timestamp.split(":")]
        print(f"Timestamp split: {timestamp_split}")
        if len(timestamp_split) == 2:
            minutes, seconds = timestamp_split
            duration = minutes * 60 + seconds
        else:
            hours, minutes, seconds = timestamp_split
            duration = hours * 3600 + minutes * 60 + seconds
        durations_in_seconds.append(duration)

    print(f"Durations in seconds: {durations_in_seconds}")
    durations_in_seconds.append(float("inf"))
    return durations_in_seconds


async def handle_youtube_link(soup, specified_link, ignore, timestamps):
    global ignore_discrepancy, custom_timestamps
    ignore_discrepancy = ignore
    custom_timestamps = timestamps
    await download_tracks(soup, specified_link)
    if download_successful:
        await split_mp3("fullAudio.mp3", track_lengths, album_folder_path)
        print("All audio cropped!")
        await write_mp3_with_metadata(soup)
