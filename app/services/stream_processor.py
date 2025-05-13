import av
import cv2
import numpy as np
from streamlit_webrtc import VideoTransformerBase
from app.core.pose_tracker import PoseDetector

class VideoProcessor(VideoTransformerBase):
    def __init__(self, current_action='pushup'):
        self.detector = PoseDetector(min_detection_confidence=0.5, min_tracking_confidence=0.5)
        self.current_action = current_action

    def update_action(self, action):
        self.current_action = action

    def recv(self, frame):
        # Convert the frame to ndarray
        image = frame.to_ndarray(format="bgr24")
        
        # Perform pose detection
        image, results = self.detector.mediapipe_detection(image, self.detector.pose)
        
        # Draw the landmarks on the image
        self.detector.draw_landmarks(image, results)

        try:
            # Get the rep count for the current exercise
            pushup_counter = self.detector.count_reps(
                image, self.current_action, results.pose_landmarks.landmark
            )
        except:
            pass
        
        # Display the rep count
        col = {
            'pushup': (245,117,16)
        }
        cv2.rectangle(image, (0,0), (640, 100), col[self.current_action], -1)
        cv2.putText(image, f'Pushup Reps: {pushup_counter}', (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
 
        # Return a VideoFrame instead of ndarray (as required by recv)
        return av.VideoFrame.from_ndarray(image, format="bgr24")