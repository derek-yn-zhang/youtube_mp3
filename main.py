"""
Modified version of sample youtube_dl script that downloads/converts a YouTube video to an MP3 file.
https://github.com/ytdl-org/youtube-dl/blob/master/README.md#embedding-youtube-dl

The script uses the yt-dlp library, which provides support for impersonating browser requests. 
This may be required for some sites that employ TLS fingerprinting (e.g. YouTube).
Directly loads cookies from browser databases (e.g. Chrome, Edge, Safari, etc.).

https://github.com/yt-dlp/yt-dlp?tab=readme-ov-file#dependencies
pip install "yt-dlp[default,curl-cffi]"

The script also embeds MP3 metadata using Mutagen.
Metadata is applied according to a configuration file and structured resources.

https://mutagen.readthedocs.io/en/latest/user/id3.html
"""

import io
import json
import argparse
from pathlib import Path

import yt_dlp
from PIL import Image
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
        self.cover_ext = Path(self.cover_path).suffix
        self.cover_mime_type = self.resolve_cover_mime_type()
        self.mp3_output_template = (
            f"{OUTPUT_DIR}/{artist} - {album}/{artist} - {track_no} - {title}"
        )
        self.mp3_output_path = self.mp3_output_template + ".mp3"

    def resolve_cover_mime_type(self):
        """Determine mime type for cover art based on file extension"""

        if self.cover_ext in [".jpg"]:
            return "image/jpg"
        if self.cover_ext in [".png"]:
            return "image/png"
        else:
            raise ValueError(
                f"Invalid cover art file extension '{self.cover_ext}', convert to '.jpg' or '.png'"
            )

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
            "cookiesfrombrowser": (BROWSER,),
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

    def resize_cover_art(self):
        """Resize thumbnail to medium quality and return byte stream"""

        img_byte_arr = io.BytesIO()
        img = Image.open(self.cover_path)
        img_resized = img.resize((300, 300), resample=Image.LANCZOS)
        img_resized.save(img_byte_arr, format=self.cover_ext[1:])
        return img_byte_arr.getvalue()

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
                # data=open(self.cover_path, mode="rb").read(),
                data=self.resize_cover_art(),
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
        "-b",
        "--browser",
        type=str,
        default="safari",
        choices=tuple(yt_dlp.cookies.SUPPORTED_BROWSERS),
        help="Browser to use for authentication (default: %(default)s)",
    )
    parser.add_argument(
        "-od",
        "--output-dir",
        type=str,
        default="downloads",
        help="Folder containing downloaded MP3 files (default: %(default)s)",
    )
    parser.add_argument(
        "-cd",
        "--cover-art-dir",
        type=str,
        default="covers",
        help="Folder containing cover art images (default: %(default)s)",
    )
    parser.add_argument(
        "-td",
        "--tracklist-dir",
        type=str,
        default="tracklists",
        help="Folder containing tracklist configuration files (default: %(default)s)",
    )
    args = parser.parse_args()

    BROWSER = args.browser
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
