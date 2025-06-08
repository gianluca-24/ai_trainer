import av
import cv2
import numpy as np
from streamlit_webrtc import VideoTransformerBase
from app.core.pose_tracker import PoseDetector

class VideoProcessor(VideoTransformerBase):
    def __init__(self, current_action='pushup'):
        self.detector = PoseDetector(min_detection_confidence=0.5, min_tracking_confidence=0.5)
        self.current_action = current_action
        self.last_error = None
        self.last_error_time = 0
        self.error_cooldown = 3  # Show each error for 3 seconds
        self.error_counter = 0  # Initialize error counter

    def update_action(self, action):
        self.current_action = action

    def get_error_count(self):
        return self.error_counter

    def recv(self, frame):
        # Convert the frame to ndarray
        image = frame.to_ndarray(format="bgr24")
        
        # Perform pose detection
        image, results = self.detector.mediapipe_detection(image, self.detector.pose)
        
        # Draw the landmarks on the image
        self.detector.draw_landmarks(image, results)

        try:
            # Get the rep count and error message for the current exercise
            pushup_counter, error_message = self.detector.count_reps(
                image, self.current_action, results.pose_landmarks.landmark
            )

            # Update error state if there's a new error
            if error_message and error_message != self.last_error:
                # add error counter only if error message is not You can start pushing up
                if error_message != "You can start pushing up": 
                    self.error_counter += 1
                self.last_error = error_message
                self.last_error_time = cv2.getTickCount()

            # Clear error after cooldown period
            if self.last_error:
                current_time = cv2.getTickCount()
                time_diff = (current_time - self.last_error_time) / cv2.getTickFrequency()
                if time_diff > self.error_cooldown:
                    self.last_error = None

        except:
            pushup_counter = 0
            self.last_error = None
        
        # Display the rep count and error count
        col = {
            'pushup': (245,117,16)
        }
        cv2.rectangle(image, (0,0), (640, 100), col[self.current_action], -1)
        cv2.putText(image, f'Pushup Reps: {pushup_counter}', (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(image, f'Form Errors: {self.error_counter}', (300, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

        # Display error message if present
        if self.last_error:
            cv2.putText(image, self.last_error, (10, 70),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
 
        # Return a VideoFrame instead of ndarray (as required by recv)
        return av.VideoFrame.from_ndarray(image, format="bgr24")