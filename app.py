import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled
from transformers import pipeline
from urllib.parse import urlparse, parse_qs
import sys
import types
import torch

# 🛠️ Fix Streamlit-Torch bug on Windows
torch.classes.__path__ = types.SimpleNamespace(_path=[])
sys.modules['torch.classes.__path__._path'] = types.SimpleNamespace()

# 🧱 Streamlit setup
st.set_page_config(page_title="YouTube Video Summarizer", layout="wide")
st.title("🎬 YouTube Video Summarizer")

# 🔍 Extract video ID from YouTube URL


@st.cache_data
def extract_video_id(url):
    query = urlparse(url)
    if query.hostname in ['www.youtube.com', 'youtube.com']:
        return parse_qs(query.query).get('v', [None])[0]
    elif query.hostname == 'youtu.be':
        return query.path[1:]
    return None

# 📜 Get transcript in English or fallback to Telugu


@st.cache_data
def get_transcript(video_id):
    try:
        return YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
    except (NoTranscriptFound, TranscriptsDisabled):
        try:
            return YouTubeTranscriptApi.get_transcript(video_id, languages=['te'])
        except ():
            raise Exception("No transcript available in English or Telugu.")

# 🧠 Load summarizer model


@st.cache_resource
def get_summarizer():
    return pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")


# 🔗 User Input
url = st.text_input("🔗 Enter YouTube URL:")

if url:
    try:
        video_id = extract_video_id(url)
        if not video_id:
            raise ValueError("Invalid YouTube URL.")

        st.video(f"https://www.youtube.com/embed/{video_id}")

        st.info("📥 Fetching transcript...")
        transcript = get_transcript(video_id)
        transcript_text = " ".join([d['text'] for d in transcript])

        with st.expander("📄 Full Transcript"):
            st.write(transcript_text)

        st.info("🧠 Generating Summary...")
        summarizer = get_summarizer()
        summary = summarizer(transcript_text[:1024], max_length=130, min_length=30, do_sample=False)[
            0]['summary_text']

        st.subheader("📌 Summary")
        st.success(summary)

    except Exception as e:
        st.error(f"⚠️ Error: {e}")
