# app/core/pose_tracker.py
import cv2
import mediapipe as mp

class PoseDetector:
    def __init__(self, min_detection_confidence=0.5, min_tracking_confidence=0.5):
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence
        self.pose = mp.solutions.pose.Pose(min_detection_confidence=self.min_detection_confidence, min_tracking_confidence=self.min_tracking_confidence)
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_pose = mp.solutions.pose

    def detect(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.pose.process(rgb)
        if results.pose_landmarks:
            self.mp_drawing.draw_landmarks(
                frame, results.pose_landmarks, self.mp_pose.POSE_CONNECTIONS
            )
        return frame

    def mediapipe_detection(self, image, model):
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image.flags.writeable = False
        results = model.process(image)
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        return image, results

    def draw_landmarks(self, image, results):
        if results.pose_landmarks:
            self.mp_drawing.draw_landmarks(
                image, results.pose_landmarks, self.mp_pose.POSE_CONNECTIONS,
                self.mp_drawing.DrawingSpec(color=(245,117,66), thickness=2, circle_radius=2),
                self.mp_drawing.DrawingSpec(color=(245,66,230), thickness=2, circle_radius=2)
            )
