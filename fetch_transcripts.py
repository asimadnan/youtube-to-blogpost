#!/usr/bin/env python3
"""
YouTube Transcript Fetcher

This script fetches transcripts from YouTube videos using yt-dlp.
It accepts YouTube URLs via command-line arguments or from a text file.
Transcripts are saved in the 'output' directory with filenames derived from video titles.

Date: 2024-04-27
"""

import os
import sys
import re
import argparse
import logging
from typing import List, Optional, Tuple
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

try:
    import webvtt
except ImportError:
    print("The 'webvtt-py' library is required to run this script.")
    print("You can install it using pip:")
    print("    pip install webvtt-py")
    sys.exit(1)

# Configuration Constants
CONFIG = {
    'DEFAULT_LANGUAGE': 'en',  # Default transcript language
    'INPUT_FILE': 'input_url.txt',
    'OUTPUT_DIR': 'data/transcripts',
    'SUBTITLES_DIR': 'temp_subtitles',  # Temporary directory for subtitles
    'LOG_FORMAT': '%(asctime)s - %(levelname)s - %(message)s',
    'YTDLP_OPTIONS': {
        'skip_download': True,
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitleslangs': ['en'],
        'subtitlesformat': 'vtt',  # You can choose 'srt' if preferred
        'outtmpl': '%(title)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
    }
}

# Setup logging
logging.basicConfig(level=logging.INFO, format=CONFIG['LOG_FORMAT'])
logger = logging.getLogger(__name__)

def parse_arguments() -> List[str]:
    """
    Parses command-line arguments to extract YouTube URLs.

    Returns:
        List[str]: A list of YouTube URLs provided via the command line.
    """
    parser = argparse.ArgumentParser(description='Fetch YouTube video transcripts.')
    parser.add_argument('urls', metavar='URL', type=str, nargs='*',
                        help='YouTube video URLs')
    args = parser.parse_args()
    return args.urls

def read_urls_from_file(file_path: str) -> List[str]:
    """
    Reads YouTube URLs from a specified text file.

    Args:
        file_path (str): Path to the text file containing YouTube URLs.

    Returns:
        List[str]: A list of YouTube URLs.
    """
    urls = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                url = line.strip()
                if url:
                    urls.append(url)
        logger.info(f"Read {len(urls)} URL(s) from '{file_path}'.")
    except FileNotFoundError:
        logger.error(f"Input file '{file_path}' not found.")
    except Exception as e:
        logger.error(f"Error reading '{file_path}': {e}")
    return urls

def is_valid_youtube_url(url: str) -> bool:
    """
    Validates whether a given URL is a valid YouTube URL.

    Args:
        url (str): The URL to validate.

    Returns:
        bool: True if valid YouTube URL, False otherwise.
    """
    youtube_regex = re.compile(
        r'^(https?://)?(www\.)?'
        r'(youtube\.com/watch\?v=|youtu\.be/)'
        r'[\w-]{11}(&\S*)?$'
    )
    return bool(youtube_regex.match(url))

def sanitize_filename(title: str) -> str:
    """
    Sanitizes the video title to create a safe filename.

    Args:
        title (str): The original video title.

    Returns:
        str: A sanitized filename with spaces replaced by dashes and special characters removed.
    """
    # Replace spaces with dashes
    filename = title.replace(' ', '-')
    # Remove characters that are invalid in filenames
    filename = re.sub(r'[\\/*?:"<>|]', '', filename)
    return filename

def fetch_transcript(url: str, language: str = CONFIG['DEFAULT_LANGUAGE']) -> Optional[Tuple[str, str]]:
    """
    Fetches the transcript for a given YouTube URL, prioritizing user-provided subtitles over auto-generated ones.
    
    Args:
        url (str): The YouTube video URL.
        language (str): The language code for the transcript.
    
    Returns:
        Optional[Tuple[str, str]]: A tuple containing the transcript text and video title if available, otherwise None.
    """
    # Step 1: Extract video information without downloading subtitles
    initial_ydl_opts = {
        'skip_download': True,
        'quiet': True,
        'no_warnings': True,
    }
    
    with YoutubeDL(initial_ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            video_title = info.get('title', 'video').strip().replace(' ', '-')
            video_title = re.sub(r'[^a-zA-Z0-9\-]', '', video_title)
            max_length = 50
            video_title = video_title[:max_length]
            subtitles = info.get('subtitles', {})
            automatic_captions = info.get('automatic_captions', {})
        except DownloadError as de:
            logger.error(f"Failed to extract video info: {de}")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred during info extraction: {e}")
            return None
    
    # Step 2: Determine subtitle availability
    if language in subtitles:
        subtitle_type = 'user-provided'
        download_subtitles = True
        write_automaticsub = False
    elif language in automatic_captions:
        subtitle_type = 'auto-generated'
        download_subtitles = True
        write_automaticsub = True
    else:
        logger.warning(f"No '{language}' subtitles available for '{video_title}'.")
        return None
    
    # Step 3: Configure yt-dlp options based on subtitle type
    ydl_opts = {
        'skip_download': True,
        'writesubtitles': download_subtitles,
        'writeautomaticsub': write_automaticsub,
        'subtitleslangs': [language],
        'subtitlesformat': 'vtt',  # Change to 'srt' if preferred
        'outtmpl': os.path.join(CONFIG['SUBTITLES_DIR'], f"{sanitize_filename(video_title)}.%(ext)s"),
        'quiet': True,
        'no_warnings': True,    
    }
    
    # Ensure the subtitles directory exists
    if not os.path.exists(CONFIG['SUBTITLES_DIR']):
        os.makedirs(CONFIG['SUBTITLES_DIR'])
        logger.debug(f"Created subtitles directory '{CONFIG['SUBTITLES_DIR']}'.")
    
    # Step 4: Download the appropriate subtitles
    with YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.extract_info(url, download=True)
        except DownloadError as de:
            logger.error(f"Failed to download {subtitle_type} subtitles: {de}")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred during subtitle download: {e}")
            return None
    
    # Step 5: Construct the expected subtitle file path
    subtitle_filename = f"{video_title}.{language}.vtt"
    subtitle_path = os.path.join(CONFIG['SUBTITLES_DIR'], subtitle_filename)
    
    if not os.path.exists(subtitle_path):
        logger.warning(f"Subtitle file '{subtitle_filename}' not found.")
        return None
    
    # Step 6: Read and convert the subtitle file to plain text
    transcript_text = convert_subtitles_to_text(subtitle_path)
    
    # Step 7: Clean up the subtitle file after processing
    try:
        os.remove(subtitle_path)
        logger.debug(f"Removed temporary subtitle file '{subtitle_filename}'.")
    except Exception as e:
        logger.warning(f"Could not remove subtitle file '{subtitle_filename}': {e}")
    
    logger.info(f"Fetched {subtitle_type} transcript for '{video_title}'.")
    return transcript_text, video_title

def convert_subtitles_to_text(subtitle_path: str) -> str:
    """
    Converts a subtitle file (VTT) to plain text without consecutive duplicate lines.

    Args:
        subtitle_path (str): Path to the subtitle file.

    Returns:
        str: The clean plain text transcript.
    """
    try:
        captions = webvtt.read(subtitle_path)
    except Exception as e:
        logger.error(f"Error reading subtitle file '{subtitle_path}': {e}")
        return ""

    transcript = []
    previous_line = ""

    for idx,caption in enumerate(captions):
        # Clean the caption text by stripping HTML tags and unnecessary whitespace
        clean_text = re.sub(r'<[^>]+>', '', caption.text).strip()
        if clean_text and idx % 2 == 0:
            transcript.append(clean_text)
    
    return '\n'.join(transcript)

def save_transcript(transcript: str, video_title: str) -> None:
    """
    Saves the transcript to a text file within the output directory.

    Args:
        transcript (str): The transcript text.
        video_title (str): The title of the YouTube video.
    """
    try:
        if not os.path.exists(CONFIG['OUTPUT_DIR']):
            os.makedirs(CONFIG['OUTPUT_DIR'])
            logger.debug(f"Created output directory '{CONFIG['OUTPUT_DIR']}'.")

        filename = sanitize_filename(video_title)[:50]  # Limit filename length
        output_path = os.path.join(CONFIG['OUTPUT_DIR'], f"{filename}.txt")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(transcript)
        logger.info(f"Transcript saved to '{output_path}'.")
    except Exception as e:
        logger.error(f"Failed to save transcript for '{video_title}': {e}")

def process_url(url: str, language: str) -> None:
    """
    Processes a single YouTube URL to fetch and save its transcript.

    Args:
        url (str): The YouTube video URL.
        language (str): The language code for the transcript.
    """
    logger.info(f"Processing URL: {url}")

    if not is_valid_youtube_url(url):
        logger.error(f"Invalid YouTube URL: {url}")
        return

    result = fetch_transcript(url, language)
    if result:
        transcript, video_title = result
        if transcript:
            save_transcript(transcript, video_title)
            return video_title
        else:
            return None
            logger.warning(f"No transcript available for '{url}'.")
    else:
        logger.warning(f"Could not retrieve transcript for '{url}'.")
        return None

def main():
    """
    The main entry point of the script.
    """
    # Parse URLs from command line
    urls = parse_arguments()

    # If no URLs provided via command line, read from input file
    if not urls:
        input_file_path = os.path.join(os.getcwd(), CONFIG['INPUT_FILE'])
        urls = read_urls_from_file(input_file_path)

    if not urls:
        logger.error("No YouTube URLs provided. Exiting.")
        sys.exit(1)

    # Process each URL
    for url in urls:
        process_url(url, CONFIG['DEFAULT_LANGUAGE'])

    # Clean up subtitles directory if empty
    try:
        if os.path.exists(CONFIG['SUBTITLES_DIR']) and not os.listdir(CONFIG['SUBTITLES_DIR']):
            os.rmdir(CONFIG['SUBTITLES_DIR'])
            logger.debug(f"Removed empty subtitles directory '{CONFIG['SUBTITLES_DIR']}'.")
    except Exception as e:
        logger.warning(f"Could not remove subtitles directory: {e}")

    logger.info("Transcript fetching completed.")

if __name__ == '__main__':
    main()