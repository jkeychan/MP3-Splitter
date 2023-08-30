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


def get_valid_filename():
    while True:
        name = input("Enter the MP3 filename: ")
        if name.lower().endswith(".mp3"):
            return name
        print("Invalid filename. Please enter a valid MP3 filename.")
        print()


def get_valid_timestamps(audio_duration):
    while True:
        timestamps = input(
            "Enter the timestamps you want to split on in milliseconds (separated by commas): ")
        timestamps = [int(t.strip()) for t in timestamps.strip().split(
            ",") if t.strip().isdigit()]
        if not timestamps:
            print(
                "Invalid timestamps. Please enter valid integer values separated by commas.")
            continue
        if timestamps != sorted(timestamps):
            print("Invalid timestamps. Please enter values in increasing order.")
            continue
        if len(set(timestamps)) != len(timestamps) or timestamps[-1] > audio_duration:
            print(
                "Invalid timestamps. Please enter unique values within the audio duration.")
            continue
        return timestamps


def create_unique_directory(path):
    i = 1
    while True:
        directory = f"{path}_{i}"
        if not os.path.exists(directory):
            os.makedirs(directory)
            return directory
        i += 1


def update_id3_tags(file_path, tags):
    audio = eyed3.load(file_path)
    if audio is not None:
        audio.tag.artist = tags.get("artist", audio.tag.artist)
        audio.tag.album = tags.get("album", audio.tag.album)
        audio.tag.title = tags.get("title", audio.tag.title)
        # Update other ID3 tags as needed
        audio.tag.save(version=eyed3.id3.ID3_V2_3)


# Check if ffmpeg is installed
ffmpeg_installed = check_ffmpeg_installed()
if not ffmpeg_installed:
    print("WARNING: ffmpeg is not installed. Please install ffmpeg for accurate MP3 parsing.")
    print("Without ffmpeg, some MP3 files may not be processed correctly.")
    proceed = input("Do you want to continue processing? (Y/N): ")
    if proceed.lower() != "y":
        exit()

# Load the audio file or directory
input_path = input(
    "Enter the path to an MP3 file or a directory containing MP3 files: ")

if os.path.isfile(input_path):  # Single MP3 file
    filenames = [input_path]
else:  # Directory of MP3 files
    filenames = [os.path.join(input_path, f) for f in os.listdir(
        input_path) if f.lower().endswith(".mp3")]

# Process each MP3 file
for filename in filenames:
    print(f"Processing: {filename}")
    # Load the audio file
    audio_file = AudioSegment.from_file(filename, format="mp3")
    audio_duration = len(audio_file)

    # Get the user-specified timestamps in milliseconds
    timestamps = get_valid_timestamps(audio_duration)

    # Split the audio file at each timestamp
    audio_file_parts = [audio_file[:timestamps[0]]]
    for i in range(1, len(timestamps)):
        audio_file_parts.append(audio_file[timestamps[i - 1]:timestamps[i]])
    audio_file_parts.append(audio_file[timestamps[-1]:])

    # Export the parts as separate files in a unique directory
    output_directory = create_unique_directory(os.path.splitext(filename)[0])
    for i, part in enumerate(audio_file_parts):
        part.export(os.path.join(output_directory,
                    f"part{i + 1}.mp3"), format="mp3")

print("Done!")

# Prompt the user to update ID3 tags
choice = input(
    "Do you want to update the ID3 tags of the exported parts? (Y/N): ").lower()
print()  # Flush the output buffer
if choice == "y":
    for root, dirs, files in os.walk(output_directory):
        for file in files:
            if file.lower().endswith(".mp3"):
                mp3_file = os.path.join(root, file)
                tags = {}
                while True:
                    print("\nCurrent tags for '{}':".format(file))
                    audio = eyed3.load(mp3_file)
                    print("Artist: {}".format(audio.tag.artist))
                    print("Album: {}".format(audio.tag.album))
                    print("Title: {}".format(audio.tag.title))
                    print("--------------------------------------")
                    print("Select a tag to update:")
                    print("   A - Artist")
                    print("   B - Album")
                    print("   T - Title")
                    print("   Q - Quit and Save")
                    choice = input("Enter your choice: ").lower()
                    print()  # Flush the output buffer
                    if choice == "q":
                        break
                    elif choice == "a":
                        tags["artist"] = input("Enter the new artist: ")
                    elif choice == "b":
                        tags["album"] = input("Enter the new album: ")
                    elif choice == "t":
                        tags["title"] = input("Enter the new title: ")

                    # Update and print the new tags
                    if tags:
                        update_id3_tags(mp3_file, tags)
                        print("\nNew tags for '{}':".format(file))
                        audio = eyed3.load(mp3_file)
                        print("Artist: {}".format(audio.tag.artist))
                        print("Album: {}".format(audio.tag.album))
                        print("Title: {}".format(audio.tag.title))
                        print("--------------------------------------")

    print("ID3 tags updated!")
