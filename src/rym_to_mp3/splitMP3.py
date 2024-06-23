import os
import ffmpeg
from mutagen.id3 import ID3, TRCK, ID3NoHeaderError

async def split_mp3(file_name, track_lengths, album_folder_path):
    print(f"Splitting {file_name} with timestamps: {track_lengths}")

    try:
        original_id3 = ID3(file_name)
    except ID3NoHeaderError:
        original_id3 = None
        print("No ID3 header found in the input file")

    for index, length in enumerate(track_lengths[:-1]):
        output_file = os.path.join(album_folder_path, f"{index}.mp3")
        open(output_file, "w").close() # Create an empty file

        print(f"File {index}.mp3 has been created successfully.")

        try:
            start_time = track_lengths[index]
            end_time = track_lengths[index + 1]

            stream = ffmpeg.input(file_name, ss=start_time)
            if end_time != float("inf"):
                stream = ffmpeg.output(
                    stream,
                    output_file,
                    codec="copy",
                    map='0:a',
                    to=end_time - start_time
                )
            else:
                stream = ffmpeg.output(
                    stream,
                    output_file,
                    codec="copy",
                    map='0:a'
                )

            ffmpeg.run(stream, overwrite_output=True)
            print(f"Audio cropped for track {index}")

            # Apply the original ID3 tags to the new file
            if original_id3 is not None:
                new_id3 = ID3(output_file)
                for tag in original_id3.values():
                    if tag.FrameID != 'TRCK':
                        new_id3.add(tag)
                
                # Set the track number to the current index
                new_id3.add(TRCK(encoding=3, text=str(index + 1)))
                new_id3.save()
                
                print(f"Metadata copied for track {index}")

        except Exception as e:
            print(f"Error cropping audio: {e}")