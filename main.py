"""
Modified version of sample youtube_dl script that downloads/converts a YouTube video to an MP3 file.
https://github.com/ytdl-org/youtube-dl/blob/master/README.md#embedding-youtube-dl

The script uses the yt-dlp library, which provides support for impersonating browser requests. 
This may be required for some sites that employ TLS fingerprinting (i.e. YouTube).
Directly loads cookies from browser databases (e.g. Chrome, Edge and Safari).

https://github.com/yt-dlp/yt-dlp?tab=readme-ov-file#dependencies
pip install "yt-dlp[default,curl-cffi]"

The script also embeds MP3 metadata using Mutagen.
Metadata is applied according to a configuration file and structured resources.

https://mutagen.readthedocs.io/en/latest/user/id3.html
"""

import json
import argparse
from pathlib import Path

import yt_dlp
from mutagen.mp3 import MP3
from mutagen.id3 import (
    ID3,
    TIT2,  # Title
    TPE1,  # Artist
    TALB,  # Album
    APIC,  # Cover
    TRCK,  # Track No.
    error,
)


class MyLogger(object):
    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        print(msg)


class YouTubeTrack:
    """Wrapper for manipulating a track and its associated metadata"""

    def __init__(
        self,
        url,
        track_no,
        title,
        artist,
        album,
        cover,
    ):
        self.url = url
        self.track_no = track_no
        self.title = title
        self.artist = artist
        self.album = album
        self.cover_path = f"{COVER_ART_DIR}/{cover}"
        self.cover_mime_type = self.resolve_cover_mime_type()
        self.mp3_output_template = (
            f"{OUTPUT_DIR}/{artist} - {album}/{artist} - {track_no} - {title}"
        )
        self.mp3_output_path = self.mp3_output_template + ".mp3"

    def resolve_cover_mime_type(self):
        """Determine mime type for cover art based on file extension"""

        cover_ext = Path(self.cover_path).suffix
        if cover_ext in [".jpg"]:
            return "image/jpg"
        if cover_ext in [".png"]:
            return "image/png"
        else:
            raise ValueError(f"Invalid cover art file format '{cover_ext}'")

    def initialize_mp3_output_path(self):
        """Create intermediate directories for mp3 path"""

        Path(self.mp3_output_template).parent.mkdir(parents=True, exist_ok=True)

    def is_downloaded(self):
        """Check if track has already been downloaded"""

        return Path(self.mp3_output_path).exists()

    def progress_hook(self, payload):
        """Log progress of download"""

        if payload["status"] == "finished":
            print("Done downloading, now converting ...")

    def extract_mp3(self):
        """Download video from url and convert to MP3"""

        yt_opts = {
            "verbose": True,  # [DEBUG]
            # "cookiesfrombrowser": ("chrome",),
            "outtmpl": self.mp3_output_template,
            "format": "bestaudio/best",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
            "logger": MyLogger(),
            "progress_hooks": [self.progress_hook],
        }
        with yt_dlp.YoutubeDL(yt_opts) as ydl:
            ydl.download([self.url])

    def write_mp3_metadata(self):
        """Add tags and album art to an MP3 file."""

        audio = MP3(self.mp3_output_path, ID3=ID3)
        audio.tags.add(TRCK(encoding=3, text=self.track_no))
        audio.tags.add(TIT2(encoding=3, text=self.title))
        audio.tags.add(TPE1(encoding=3, text=self.artist))
        audio.tags.add(TALB(encoding=3, text=self.album))
        audio.tags.add(
            APIC(
                encoding=3,  # 3 is for utf-8
                mime=self.cover_mime_type,  # Can be image/jpeg or image/png
                type=3,  # 3 is for the cover image
                desc="Cover",
                data=open(self.cover_path, mode="rb").read(),
            )
        )
        audio.save()

    def fetch(self):
        """Main method for the class"""

        if self.is_downloaded():
            print(f"Already downloaded: {self.mp3_output_path}")
        else:
            self.initialize_mp3_output_path()
            self.extract_mp3()
            self.write_mp3_metadata()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--tracklist", type=str, help="Tracklist file name")
    parser.add_argument(
        "-od",
        "--output-dir",
        type=str,
        default="downloads",
        help="Folder containing downloaded MP3 files",
    )
    parser.add_argument(
        "-cd",
        "--cover-art-dir",
        type=str,
        default="covers",
        help="Folder containing cover art images",
    )
    parser.add_argument(
        "-td",
        "--tracklist-dir",
        type=str,
        default="tracklists",
        help="Folder containing tracklist configuration files",
    )
    args = parser.parse_args()

    OUTPUT_DIR = args.output_dir
    COVER_ART_DIR = args.cover_art_dir
    TRACKLIST_DIR = args.tracklist_dir
    TRACKLIST_FILE = args.tracklist
    TRACKLIST_PATH = f"{TRACKLIST_DIR}/{TRACKLIST_FILE}"

    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    tracklist = json.load(open(TRACKLIST_PATH, "r"))

    for track in tracklist:
        print(json.dumps(track, indent=4))
        YouTubeTrack(**track).fetch()
