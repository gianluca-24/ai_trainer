# app/services/stream_processor.py
import av
from streamlit_webrtc import VideoTransformerBase
from app.core.pose_tracker import PoseDetector

class VideoProcessor(VideoTransformerBase):
    def __init__(self):
        self.detector = PoseDetector(min_detection_confidence=0.5, min_tracking_confidence=0.5)

    def transform(self, frame):
        image = frame.to_ndarray(format="bgr24")
        image, results = self.detector.mediapipe_detection(image, self.detector.pose)
        self.detector.draw_landmarks(image, results)
        return image