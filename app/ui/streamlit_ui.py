# app/ui/streamlit_ui.py 
import streamlit as st
from streamlit_webrtc import webrtc_streamer
from app.services.stream_processor import VideoProcessor

def run():
    st.title("📹 Real-time AI personal trainer 🏋🏻‍♂️")
    
    exercise = st.radio(
        "Choose the exercise:",
        ('pushup')
    )

    # Create containers for stats
    col1, col2 = st.columns(2)
    with col1:
        error_placeholder = st.empty()
    with col2:
        stats_placeholder = st.empty()

    ctx = webrtc_streamer(
        key="pose-detection",
        video_processor_factory=VideoProcessor,
        media_stream_constraints={"video": True, "audio": False},
        async_processing=True,
    )

    if ctx.video_processor:
        ctx.video_processor.update_action(exercise)

        # Access error messages and stats from the video processor
        if hasattr(ctx.video_processor, 'last_error') and ctx.video_processor.last_error:
            error_placeholder.error(ctx.video_processor.last_error)
        
        # Display error statistics
        error_count = ctx.video_processor.get_error_count()
        stats_placeholder.metric(
            label="Form Errors",
            value=error_count,
            delta=None,
            delta_color="inverse"  # Red for positive (more errors), green for negative (fewer errors)
        )