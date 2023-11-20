import subprocess
from dotenv import load_dotenv
import re
import math
from datetime import timedelta
from pydub import AudioSegment
import os
from openai import OpenAI
client = OpenAI()


# Define constants
AUDIO_FOLDER = "audio"
TRANSCRIPTS_FOLDER = "transcripts"
AUDIO_FORMAT = "wav"
# 20 minutes in milliseconds, adjusted as per your comment
TIME_CHUNK_MS = 20 * 60 * 1000
MAX_SIZE_MB = 25
BIT_RATE = "128k"  # Adjust the bit rate here
OUTPUT_FORMAT = "mp3"  # Specify the output format
RESPONSE_FORMAT = "vtt"

# Utility functions for SRT timestamp parsing and conversion


def parse_srt_timestamp(time_str):
    h, m, s, ms = map(int, re.split('[:,]', time_str))
    return timedelta(hours=h, minutes=m, seconds=s, milliseconds=ms).total_seconds() * 1000


def parse_vtt_timestamp(time_str):
    h, m, s, ms = map(int, re.split('[.:]', time_str))
    return timedelta(hours=h, minutes=m, seconds=s, milliseconds=ms).total_seconds() * 1000


def convert_ms_to_srt_timestamp(ms):
    s, ms = divmod(ms, 1000)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    return f"{int(h):02}:{int(m):02}:{int(s):02},{int(ms):03}"


def convert_ms_to_vtt_timestamp(ms):
    s, ms = divmod(ms, 1000)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    return f"{int(h):02}:{int(m):02}:{int(s):02}.{int(ms):03}"


def extract_audio_from_video(video_file_path):
    base_file_name = os.path.basename(video_file_path)
    wav_file = f"audio/{base_file_name[:-4]}.{AUDIO_FORMAT}"
    try:
        subprocess.call(['ffmpeg', '-i', video_file_path, '-f',
                        AUDIO_FORMAT, '-vn', wav_file, '-y', '-ab', BIT_RATE])
    except Exception as e:
        print(f"Error converting {video_file_path} to WAV: {e}")
        return None
    return wav_file


def transcribe_and_merge(audio_file):
    base_file_name = os.path.basename(audio_file)
    os.makedirs(f'{AUDIO_FOLDER}/{base_file_name[:-4]}', exist_ok=True)
    os.makedirs(f'{TRANSCRIPTS_FOLDER}/{base_file_name[:-4]}', exist_ok=True)
    audio = AudioSegment.from_file(audio_file)

    file_size = len(audio) * (int(BIT_RATE.replace("k", "")) / 8) / 1024
    chunk_names = []
    if file_size > (MAX_SIZE_MB * 1024 * 1024):
        parts = math.ceil(len(audio) / TIME_CHUNK_MS)
        chunk_length = len(audio) // parts
        for i in range(parts):
            chunk = audio[i * chunk_length: (i + 1) * chunk_length]
            chunk_name = f"{AUDIO_FOLDER}/{base_file_name[:-4]}/chunk{i}.{OUTPUT_FORMAT}"
            chunk.export(chunk_name, format=OUTPUT_FORMAT, bitrate=BIT_RATE)
            chunk_names.append(chunk_name)
    else:
        chunk_name = f"{AUDIO_FOLDER}/{base_file_name[:-4]}/chunk0.{OUTPUT_FORMAT}"
        audio.export(chunk_name, format=OUTPUT_FORMAT, bitrate=BIT_RATE)
        chunk_names.append(chunk_name)

    merged_transcript = ""
    cumulative_duration_ms = 0
    for chunk_name in chunk_names:
        with open(chunk_name, 'rb') as audio_chunk:
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_chunk,
                response_format=RESPONSE_FORMAT
            )
            transcript_text = response

        chunk_base = os.path.basename(chunk_name)[:-len(AUDIO_FORMAT)-1]
        transcript_path = f"{TRANSCRIPTS_FOLDER}/{base_file_name[:-4]}/{chunk_base}.{RESPONSE_FORMAT}"
        with open(transcript_path, "w") as f:
            f.write(transcript_text)
        if RESPONSE_FORMAT == "vtt":
            for line in transcript_text.split('\n'):
                if '-->' in line:
                    start, end = line.split(' --> ')
                    start_ms = parse_vtt_timestamp(
                        start) + cumulative_duration_ms
                    end_ms = parse_vtt_timestamp(end) + cumulative_duration_ms
                    merged_transcript += f"{convert_ms_to_vtt_timestamp(start_ms)} --> {convert_ms_to_vtt_timestamp(end_ms)}\n"
                else:
                    merged_transcript += line + '\n'
        elif RESPONSE_FORMAT == "srt":
            for line in transcript_text.split('\n'):
                if '-->' in line:
                    start, end = line.split(' --> ')
                    start_ms = parse_srt_timestamp(
                        start) + cumulative_duration_ms
                    end_ms = parse_srt_timestamp(end) + cumulative_duration_ms
                    merged_transcript += f"{convert_ms_to_srt_timestamp(start_ms)} --> {convert_ms_to_srt_timestamp(end_ms)}\n"
                else:
                    merged_transcript += line + '\n'
        cumulative_duration_ms += len(audio) // len(chunk_names)

    merged_transcript_path = f"{TRANSCRIPTS_FOLDER}/{base_file_name[:-4]}/merged_transcript.{RESPONSE_FORMAT}"
    with open(merged_transcript_path, "w") as file:
        file.write(merged_transcript)
    return merged_transcript_path


def transcribe(media_file):
    os.makedirs(AUDIO_FOLDER, exist_ok=True)
    os.makedirs(TRANSCRIPTS_FOLDER, exist_ok=True)
    if media_file.endswith(".mp4") or media_file.endswith(".mov") or media_file.endswith(".webm"):
        wav_file = extract_audio_from_video(media_file)
    elif media_file.endswith(".wav") or media_file.endswith(".mp3") or media_file.endswith(".m4a"):
        wav_file = media_file
    if wav_file:
        merged_transcript_path = transcribe_and_merge(wav_file)
        return merged_transcript_path
    else:
        return None


if __name__ == "__main__":
    os.makedirs(AUDIO_FOLDER, exist_ok=True)
    os.makedirs(TRANSCRIPTS_FOLDER, exist_ok=True)
    mp4_file = "uploads/GMT20231117-020828_Recording_640x360.mp4"
    wav_file = extract_audio_from_video(mp4_file)
    if wav_file:
        transcribe_and_merge(wav_file)
