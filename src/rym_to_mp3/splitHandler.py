import os
import re

from .splitMP3 import split_mp3

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

async def handle_split_request(file_name, timestamps):
    if (file_name.endswith(".mp3")):
          file_name =file_name.replace(".mp3", "")
    
    # Make a directory with the same name as the file to dump the split audio
    if not os.path.exists(file_name):
            os.makedirs(file_name)
            return
    
    track_lengths = handle_custom_timestamps(timestamps)
    print(track_lengths)

    await split_mp3(file_name + ".mp3", track_lengths, file_name)
