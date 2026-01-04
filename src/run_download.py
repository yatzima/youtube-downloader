import argparse
import os
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import yt_dlp

# Default settings
DEFAULT_AUDIO_FORMAT = "mp3"
DEFAULT_DOWNLOAD_DIR = "../downloads"
DEFAULT_QUALITY = "320k"


class YouTubeDownloader:
    def __init__(
        self,
        output_dir=DEFAULT_DOWNLOAD_DIR,
        audio_format=DEFAULT_AUDIO_FORMAT,
        quality=DEFAULT_QUALITY,
    ):
        """
        Initialize the downloader.

        Args:
            output_dir (str): Directory to save files
            audio_format (str): Output format (wav, flac, mp3)
            quality (str): Audio quality (320k, 256k, 192k for mp3; best for wav/flac)
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.audio_format = audio_format.lower()
        self.quality = quality

        # Configure yt-dlp options for high-quality audio
        self.ydl_opts = {
            "format": "bestaudio/best",  # Download best quality audio
            "outtmpl": str(self.output_dir / "%(title)s.%(ext)s"),
            "extractaudio": True,
            "audioformat": self.audio_format,
            "audioquality": (
                self.quality if self.audio_format == "mp3" else "0"
            ),  # 0 = best for wav/flac
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": self.audio_format,
                    "preferredquality": (
                        self.quality if self.audio_format == "mp3" else None
                    ),
                }
            ],
            "ffmpeg_location": None,  # Will use system ffmpeg
        }

        # Add format-specific options
        if self.audio_format in ["wav", "flac"]:
            self.ydl_opts["postprocessors"][0]["preferredquality"] = None  # Lossless

        # Clean filename template
        self.ydl_opts["outtmpl"] = str(
            self.output_dir / "%(uploader)s - %(title)s.%(ext)s"
        )

    def sanitize_filename(self, filename):
        """Remove invalid characters from filename."""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, "_")
        return filename

    def download_single_video(self, url):
        """Download a single YouTube video as audio."""
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                # Get video info first
                info = ydl.extract_info(url, download=False)
                title = info.get("title", "Unknown")
                uploader = info.get("uploader", "Unknown")
                duration = info.get("duration", 0)

                print(f"Title: {title}")
                print(f"Uploader: {uploader}")
                print(f"Duration: {duration // 60}:{duration % 60:02d}")
                print(f"Downloading...")

                # Download and convert
                ydl.download([url])
                print(f"✓ Successfully downloaded: {title}")
                return True

        except Exception as e:
            print(f"✗ Error downloading {url}: {str(e)}")
            return False

    def download_playlist(self, url):
        """Download all videos from a YouTube playlist."""
        playlist_opts = self.ydl_opts.copy()
        playlist_opts["extract_flat"] = False

        try:
            with yt_dlp.YoutubeDL(playlist_opts) as ydl:
                # Get playlist info
                info = ydl.extract_info(url, download=False)
                playlist_title = info.get("title", "Unknown Playlist")
                entries = info.get("entries", [])

                print(f"Playlist: {playlist_title}")
                print(f"Found {len(entries)} videos")
                print("-" * 50)

                # Create playlist subdirectory
                playlist_dir = self.output_dir / self.sanitize_filename(playlist_title)
                playlist_dir.mkdir(exist_ok=True)

                # Update output template for playlist
                playlist_opts["outtmpl"] = str(
                    playlist_dir
                    / "%(playlist_index)02d - %(title)s.%(ext)s"  # Numbered format
                    # playlist_dir / "%(title)s.%(ext)s" # Non-numbered format
                )

                # Download playlist
                with yt_dlp.YoutubeDL(playlist_opts) as playlist_ydl:
                    playlist_ydl.download([url])

                print(f"✓ Playlist download complete!")
                return True

        except Exception as e:
            print(f"✗ Error downloading playlist {url}: {str(e)}")
            return False

    def is_playlist(self, url):
        """Check if URL is a playlist."""
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        return "list" in query_params

    def download(self, urls):
        """Download one or more YouTube URLs."""
        if isinstance(urls, str):
            urls = [urls]

        successful = 0
        total = len(urls)

        for i, url in enumerate(urls, 1):
            print(f"\n[{i}/{total}] Processing: {url}")

            if self.is_playlist(url):
                success = self.download_playlist(url)
            else:
                success = self.download_single_video(url)

            if success:
                successful += 1

        print(f"\n" + "=" * 50)
        print(f"Download Summary: {successful}/{total} successful")
        print(f"Files saved to: {self.output_dir.absolute()}")


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Download YouTube videos as high-quality audio for DJing"
    )
    parser.add_argument("urls", nargs="+", help="YouTube URLs to download")
    parser.add_argument(
        "-o",
        "--output",
        default=DEFAULT_DOWNLOAD_DIR,
        help="Output directory (default: downloads)",
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=["wav", "flac", "mp3"],
        default=DEFAULT_AUDIO_FORMAT,
        help="Audio format (default: wav)",
    )
    parser.add_argument(
        "-q",
        "--quality",
        default=DEFAULT_QUALITY,
        help="Audio quality for MP3 (default: 320k). Ignored for WAV/FLAC.",
    )
    return parser.parse_args()


def main():
    # Parser command line arguments
    args = parse_arguments()

    # Check if ffmpeg is available
    if os.system("ffmpeg -version > /dev/null 2>&1") != 0:
        print("Error: ffmpeg not found. Please install ffmpeg first.")
        print("On Ubuntu/Debian: sudo apt install ffmpeg")
        print("On macOS: brew install ffmpeg")
        print("On Windows: Download from https://ffmpeg.org/download.html")
        sys.exit(1)

    # Initialize downloader
    downloader = YouTubeDownloader(
        output_dir=args.output, audio_format=args.format, quality=args.quality
    )

    # Download
    downloader.download(args.urls)


if __name__ == "__main__":
    # Example usage if run directly
    if len(sys.argv) == 1:
        print("YouTube to Audio Converter")
        print("=" * 40)
        print("Usage examples:")
        print("python youtube_dj.py 'https://www.youtube.com/watch?v=VIDEO_ID'")
        print("python youtube_dj.py -f mp3 -q 320k 'URL1' 'URL2'")
        print("python youtube_dj.py -o my_music -f flac 'PLAYLIST_URL'")
        print("\nInstall dependencies with:")
        print("pip install yt-dlp")
        print("\nRequires ffmpeg to be installed on your system.")
    else:
        main()
