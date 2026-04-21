#!/usr/bin/env python3
"""Fetch a YouTube video's transcript and save it as a text file.

Usage:
    python tools/get_transcript.py <youtube-url-or-video-id> [-o output.txt]

If no -o flag is given, prints to stdout. Pair with /extract-transcript to
go from YouTube URL to structured Markdown in one flow.
"""

import argparse
import re
import sys

from youtube_transcript_api import YouTubeTranscriptApi


def extract_video_id(url_or_id: str) -> str:
    """Pull the 11-char video ID from any common YouTube URL format."""
    patterns = [
        r"(?:v=|/v/|youtu\.be/)([A-Za-z0-9_-]{11})",
        r"^([A-Za-z0-9_-]{11})$",
    ]
    for pat in patterns:
        m = re.search(pat, url_or_id)
        if m:
            return m.group(1)
    return url_or_id  # fall through — let the API error if invalid


def fetch_transcript(video_id: str) -> str:
    api = YouTubeTranscriptApi()
    transcript = api.fetch(video_id)
    return "\n".join(snippet.text for snippet in transcript)


def main():
    parser = argparse.ArgumentParser(description="Fetch a YouTube transcript.")
    parser.add_argument("url", help="YouTube URL or video ID")
    parser.add_argument("-o", "--output", help="Write to file instead of stdout")
    args = parser.parse_args()

    video_id = extract_video_id(args.url)
    text = fetch_transcript(video_id)

    if args.output:
        with open(args.output, "w") as f:
            f.write(text)
        print(f"Saved transcript to {args.output}", file=sys.stderr)
    else:
        print(text)


if __name__ == "__main__":
    main()
