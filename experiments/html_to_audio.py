from bs4 import BeautifulSoup
from pydub import AudioSegment
import os
import subprocess
import re

def extract_text_blocks(html_path):
    with open(html_path, 'r') as file:
        html_content = file.read()
    soup = BeautifulSoup(html_content, 'html.parser')
    text_blocks = soup.find_all('p')  # Adjust the tag as needed
    return [block.get_text() for block in text_blocks if block.get_text() != '']

def text_to_speech(text_blocks, output_dir):
    audio_files = []
    for i, text in enumerate(text_blocks):
        print(f"Processing block {i + 1}/{len(text_blocks)}"
                f" - {round((i + 1) / len(text_blocks) * 100, 2)}%")
        text_file_path = os.path.join(output_dir, f"text_{i}.txt")
        audio_file_path = os.path.join(output_dir, f"audio_{i}.aiff")
        with open(text_file_path, 'w') as text_file:
            text_file.write(text)
        command = f"say --input-file {text_file_path} --progress --output-file {audio_file_path}"
        subprocess.run(command, shell=True)
        audio_files.append(audio_file_path)
    return audio_files

import subprocess
from subprocess import TimeoutExpired

def find_next_audio_file_index(output_dir):
    """
    Finds the highest index of existing audio files in the output directory
    and returns the next index to start from.
    """
    existing_files = os.listdir(output_dir)
    audio_indices = [int(re.search(r"audio_(\d+).aiff", file).group(1))
                     for file in existing_files if re.match(r"audio_\d+.aiff", file)]
    next_index = max(audio_indices) + 1 if audio_indices else 0
    return next_index

def text_to_speech_resume(text_blocks, output_dir, timeout_seconds=30, retry_attempts=3):
    audio_files = []
    start_index = find_next_audio_file_index(output_dir)
    for i in range(start_index, len(text_blocks)):
        print(f"Processing block {i + 1}/{len(text_blocks)}"
                f" - {round((i + 1) / len(text_blocks) * 100, 2)}%")
        text = text_blocks[i]
        text_file_path = os.path.join(output_dir, f"text_{i}.txt")
        audio_file_path = os.path.join(output_dir, f"audio_{i}.aiff")
        with open(text_file_path, 'w') as text_file:
            text_file.write(text)
        
        command = f"say --input-file {text_file_path} --progress --output-file {audio_file_path}"
        for attempt in range(retry_attempts):
            try:
                subprocess.run(command, shell=True, timeout=timeout_seconds)
                break  # Command succeeded, break out of the retry loop
            except TimeoutExpired:
                print(f"Command timed out on attempt {attempt + 1}. Retrying...")
                if attempt == retry_attempts - 1:
                    print("Max retry attempts reached. Skipping this text block.")
                    # Optionally handle the failure, e.g., by continuing to the next block or stopping the script
        else:
            # All retries failed; handle accordingly
            continue  # In this case, just continue to the next text block
        
        audio_files.append(audio_file_path)
    return audio_files

def splice_audio(audio_files, final_output_path):
    combined = AudioSegment.empty()
    for audio_file in audio_files:
        audio_segment = AudioSegment.from_file(audio_file)
        combined += audio_segment
    combined.export(final_output_path, format="mp3")

def main(html_path, output_dir):
    text_blocks = extract_text_blocks(html_path)
    audio_files = text_to_speech_resume(text_blocks, output_dir)
    final_output_path = os.path.join(output_dir, "final_audio.mp3")
    splice_audio(audio_files, final_output_path)
    print(f"Final audio file created at {final_output_path}")

# Usage example
html_path = '/Users/jamescourson/Downloads/Newbigin Thomas West New.html'
output_dir = '/Users/jamescourson/Downloads/NewbiginAudio'
num_blocks = 5  # Number of text blocks to process
main(html_path, output_dir)