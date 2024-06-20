import os
import re
import requests
from mutagen.id3 import ID3, APIC, TALB, TPE1, TPE2, TRCK, TIT2, TYER, TCON, TPOS

async def data_to_metadata(soup):
    track_list = soup.select("#tracks li.track")

    # Prune tracklist for any bad tracks
    pruned_track_list = []
    for element in track_list:
        duration_span = element.select_one('span.tracklist_duration')
        if duration_span:
            duration = int(duration_span.get('data-inseconds', 0))
            if duration != 0:
                pruned_track_list.append(element)

    # Remove the last track
    # if pruned_track_list:
    #     pruned_track_list.pop()

    album = soup.select_one(".album_title").get_text().split('\n')[0].strip()
    artists = [artist.get_text(strip=True) for artist in soup.select("span[itemprop='byArtist'] a.artist")]
    artist_texts = "\0".join(artists)
    genres = [genre.get_text(strip=True) for genre in soup.select("span.release_pri_genres a.genre")]
    genre_texts = "\0".join(genres)

    featured_artist_texts = []
    for element in pruned_track_list:
        featured_artists = [artist.get_text(strip=True) for artist in element.select("li.featured_credit a.artist")]
        featured_artist_texts.append("\0".join(featured_artists))

    year_href = soup.select_one("a[href^='/charts/top/']").get("href", "")
    year = year_href.split("/")[-1] if year_href else ""
    image_url = soup.select_one("img[alt^='Cover art']").get("src", "")
    if image_url:
        image_url = image_url[2:]

    image_response = requests.get(f"https://{image_url}")
    if image_response.status_code == 200:
        image_data = image_response.content
    else:
        image_data = None

    metadata = []

    # Actually apply the metadata to the tracks
    for index, element in enumerate(pruned_track_list):
        title = element.select_one("span.tracklist_title").get_text().split("\n")[0].strip()
        track_artists = artist_texts
        if featured_artist_texts[index]:
            track_artists += "\0" + featured_artist_texts[index]
        disc_number = 1
        track_number_text = element.select_one("span.tracklist_num").get_text(strip=True)
        if "." in track_number_text:
            disc_number, track_number = map(int, track_number_text.split("."))
            print(f"Disc number {disc_number}")
        else:
            track_number = index + 1
        track_metadata = {
            "title": title,
            "performer_info": track_artists,
            "album": album,
            "year": year,
            "genre": genre_texts,
            "track_number": track_number,
            "disc_number": disc_number,
            "image_data": image_data,
        }
        metadata.append(track_metadata)

    return metadata


async def write_mp3_with_metadata(data):
    metadata_array = await data_to_metadata(data)

    for index, metadata in enumerate(metadata_array):
        input_file = os.path.join(metadata["album"], f"{index}.mp3")

        try:
            audio = ID3(input_file)
        except Exception as e:
            print(f"Error reading ID3 tags: {e}")
            continue

        # Set the metadata
        audio.clear()
        audio.add(TIT2(encoding=3, text=metadata["title"]))
        audio.add(TPE1(encoding=3, text=metadata["performer_info"].split("\0")))
        audio.add(TALB(encoding=3, text=metadata["album"]))
        audio.add(TYER(encoding=3, text=metadata["year"]))
        audio.add(TCON(encoding=3, text=metadata["genre"].split("\0")))
        audio.add(TRCK(encoding=3, text=f"{metadata['track_number']}"))
        audio.add(TPOS(encoding=3, text=f"{metadata['disc_number']}"))

        if metadata["image_data"]:
            audio.add(
                APIC(
                    encoding=3,
                    mime="image/jpeg",
                    type=3,
                    desc="Cover",
                    data=metadata["image_data"],
                )
            )

        audio.save()

        sanitized_title = re.sub(r"[^a-zA-Z0-9\-]", "-", metadata["title"].lower())
        output_file = os.path.join(metadata["album"], f"{sanitized_title}.mp3")
        os.rename(input_file, output_file)
        print(f"Metadata written to {sanitized_title}.mp3")