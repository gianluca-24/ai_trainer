# app/ui/streamlit_ui.py
import streamlit as st
from streamlit_webrtc import webrtc_streamer
from app.services.stream_processor import VideoProcessor

def run():
    st.title("📹 Real-time Body Tracking with MediaPipe")

    webrtc_streamer(
        key="pose-detection",
        video_processor_factory=VideoProcessor,
        media_stream_constraints={"video": True, "audio": False},
        async_processing=True,
    )