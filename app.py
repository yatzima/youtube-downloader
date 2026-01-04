import os
import subprocess
import pandas as pd
import streamlit as st


def run_and_display_stdout(*cmd_with_args):
    result = subprocess.Popen(cmd_with_args, stdout=subprocess.PIPE)
    for line in iter(lambda: result.stdout.readline(), b""):
        st.text(line.decode("utf-8"))
    # st.code(line.decode("utf-8"), language="bash")
    # st.write_stream(iter(lambda: result.stdout.readline(), b""))


# Page config
st.set_page_config(
    page_title="YouTube Downloader",
    page_icon="🎧",
    layout="centered",
    initial_sidebar_state="expanded",
)


# Header
st.markdown(
    "<h1 class='main-header'>🎧 YouTube Downloader</h1>", unsafe_allow_html=True
)
st.markdown("**Download YouTube videos as high-quality audio files**")

# Sidebar for settings
with st.sidebar:
    st.header("⚙️ Settings")

    audio_format = st.selectbox(
        "Audio Format",
        ["MP3 (Lossy)", "WAV (Lossless)", "FLAC (Lossless)"],
        index=0,
        help="WAV and FLAC are lossless formats, best for DJing",
    )

    # Map display names to actual formats
    format_map = {
        "WAV (Lossless)": "wav",
        "FLAC (Lossless)": "flac",
        "MP3 (Lossy)": "mp3",
    }
    selected_format = format_map[audio_format]

    if selected_format == "mp3":
        quality = st.selectbox(
            "MP3 Quality",
            ["320k", "256k", "192k", "128k"],
            index=0,
        )
    else:
        quality = "best"
        st.info("Lossless formats use best available quality")

    st.markdown("---")
    st.markdown("**💡 Tips:**")
    st.markdown("- WAV files are larger but highest quality")
    st.markdown("- FLAC offers good compression with no quality loss")
    st.markdown("- MP3 320k is good for most DJ applications")
    st.markdown("- Playlists will be downloaded as a ZIP file")

# Main interface
st.markdown("### 📥 Download Audio")

# URL input
url = st.text_input(
    "YouTube URL",
    placeholder="https://www.youtube.com/watch?v=...",
    help="Enter a YouTube video or playlist URL",
)

# Download button
if st.button("🎵 Download Audio", type="primary"):
    if not url:
        st.error("Please enter a YouTube URL")

    if not url.startswith(
        (
            "https://www.youtube.com/",
            "https://youtube.com/",
            "https://youtu.be/",
            "https://music.youtube",
        )
    ):
        st.error("Please enter a valid YouTube URL")

    # Check if ffmpeg is available
    if os.system("ffmpeg -version > /dev/null 2>&1") != 0:
        st.error("""
        **FFmpeg not found!** 
        
        Please install ffmpeg first:
        - **Ubuntu/Debian**: `sudo apt install ffmpeg`
        - **macOS**: `brew install ffmpeg` 
        - **Windows**: Download from https://ffmpeg.org/download.html
        """)

    # Show progress
    with st.spinner("Processing download..."):
        try:
            # Run the script file
            run_and_display_stdout(
                # "/opt/anaconda3/envs/youtube-downloader/bin/python3",
                "/opt/anaconda3/bin/python/",
                "run_download.py",
                "-f",
                selected_format,
                "-q",
                quality,
                f"{url}",
            )
            st.success("Download completed successfully!")
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            raise e
