import os
import subprocess
from pydub import AudioSegment
import eyed3


def check_ffmpeg_installed():
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def get_valid_timestamps(audio_duration):
    while True:
        timestamps = input(
            "Enter the timestamps in milliseconds (separated by commas): ").split(",")
        timestamps = [int(t.strip()) for t in timestamps if t.strip(
        ).isdigit() and 0 <= int(t) <= audio_duration]

        if timestamps == sorted(set(timestamps)):
            return timestamps
        else:
            print(
                "Invalid timestamps. Ensure they are in increasing order, unique, and within audio duration.")


def create_unique_directory(path):
    i = 1
    while os.path.exists(f"{path}_{i}"):
        i += 1
    os.makedirs(f"{path}_{i}")
    return f"{path}_{i}"


def edit_id3_tags(mp3_file):
    tags = {}
    audio = eyed3.load(mp3_file)
    while True:
        print("\nCurrent tags for '{}':".format(mp3_file))
        print("Artist: {}".format(audio.tag.artist))
        print("Album: {}".format(audio.tag.album))
        print("Title: {}".format(audio.tag.title))
        print("-------- Select a tag to update or Q to save and quit --------")
        choice = input("A - Artist, B - Album, T - Title, Q - Quit: ").lower()
        if choice == 'a':
            tags["artist"] = input("Enter the new artist: ")
        elif choice == 'b':
            tags["album"] = input("Enter the new album: ")
        elif choice == 't':
            tags["title"] = input("Enter the new title: ")
        elif choice == 'q':
            break

    if tags:
        audio.tag.artist = tags.get("artist", audio.tag.artist)
        audio.tag.album = tags.get("album", audio.tag.album)
        audio.tag.title = tags.get("title", audio.tag.title)
        audio.tag.save()


if not check_ffmpeg_installed():
    print("WARNING: ffmpeg is not installed. Install ffmpeg for accurate MP3 parsing.")
    if input("Continue without ffmpeg? (Y/N): ").lower() != "y":
        exit()

input_path = input("Enter the path to an MP3 file or directory of MP3s: ")
filenames = [input_path] if os.path.isfile(input_path) else [os.path.join(
    input_path, f) for f in os.listdir(input_path) if f.lower().endswith(".mp3")]

for filename in filenames:
    audio_file = AudioSegment.from_file(filename, format="mp3")
    timestamps = get_valid_timestamps(len(audio_file))

    audio_segments = [audio_file[:timestamps[0]]] + [audio_file[timestamps[i]:timestamps[i+1]]
                                                     for i in range(len(timestamps)-1)] + [audio_file[timestamps[-1]:]]

    output_directory = create_unique_directory(os.path.splitext(filename)[0])
    for idx, segment in enumerate(audio_segments):
        segment.export(os.path.join(output_directory,
                       f"part{idx + 1}.mp3"), format="mp3")

print("Splitting done!")

if input("Update ID3 tags for the new files? (Y/N): ").lower() == "y":
    for root, _, files in os.walk(output_directory):
        for file in files:
            if file.lower().endswith(".mp3"):
                edit_id3_tags(os.path.join(root, file))
    print("ID3 tags updated!")
