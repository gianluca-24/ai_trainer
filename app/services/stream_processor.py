import av
import cv2
from streamlit_webrtc import VideoTransformerBase
from app.core.pose_tracker import PoseDetector

class VideoProcessor(VideoTransformerBase):
    def __init__(self, current_action='curl'):
        self.detector = PoseDetector(min_detection_confidence=0.5, min_tracking_confidence=0.5)
        self.current_action = current_action

    def transform(self, frame):
        # Convert the frame to ndarray
        image = frame.to_ndarray(format="bgr24")
        
        # Perform pose detection
        image, results = self.detector.mediapipe_detection(image, self.detector.pose)
        
        # Draw the landmarks on the image
        self.detector.draw_landmarks(image, results)
        
        # Get the rep count for the current exercise (e.g., 'curl', 'press', 'squat')
        curl_counter, press_counter, squat_counter = self.detector.count_reps(image, self.current_action, results.pose_landmarks)
        
        # Display the rep count on the image (Optional: you can choose where to display the count)
        cv2.putText(image, f'Curl Reps: {curl_counter}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(image, f'Press Reps: {press_counter}', (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(image, f'Squat Reps: {squat_counter}', (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        
        # Return the modified image with rep counts displayed
        return image