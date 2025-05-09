# app/core/pose_tracker.py
import math
import cv2
import mediapipe as mp
import numpy as np

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
    def calculate_angle(self, a, b, c):
        """
        Computes 3D joint angle inferred by 3 keypoints and their relative positions to one another
        """
        a = np.array(a)  # First
        b = np.array(b)  # Mid
        c = np.array(c)  # End

        radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
        angle = np.abs(radians * 180.0 / np.pi)

        if angle > 180.0:
            angle = 360 - angle

        return angle

    def get_coordinates(self, landmarks, side, joint):
        """
        Retrieves x and y coordinates of a particular keypoint from the pose estimation model
        """
        coord = getattr(self.mp_pose.PoseLandmark, side.upper() + "_" + joint.upper())
        x_coord_val = landmarks[coord.value].x
        y_coord_val = landmarks[coord.value].y
        return [x_coord_val, y_coord_val]

    def viz_joint_angle(self, image, angle, joint):
        """
        Displays the joint angle value near the joint within the image frame
        """
        cv2.putText(image, str(int(angle)),
                    tuple(np.multiply(joint, [640, 480]).astype(int)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2, cv2.LINE_AA)
        return image

    def count_reps(self, image, current_action, landmarks):
        """
        Counts repetitions of each exercise. Global count and stage (i.e., state) variables are updated within this function.
        """
        global curl_counter, press_counter, squat_counter, curl_stage, press_stage, squat_stage

        if current_action == 'curl':
            # Get coords
            shoulder = self.get_coordinates(landmarks, 'left', 'shoulder')
            elbow = self.get_coordinates(landmarks, 'left', 'elbow')
            wrist = self.get_coordinates(landmarks, 'left', 'wrist')

            # Calculate elbow angle
            angle = self.calculate_angle(shoulder, elbow, wrist)

            # Curl counter logic
            if angle < 30:
                curl_stage = "up"
            if angle > 140 and curl_stage == 'up':
                curl_stage = "down"
                curl_counter += 1
            press_stage = None
            squat_stage = None

            # Visualize joint angle
            self.viz_joint_angle(image, angle, elbow)

        elif current_action == 'press':
            # Get coords
            shoulder = self.get_coordinates(landmarks, 'left', 'shoulder')
            elbow = self.get_coordinates(landmarks, 'left', 'elbow')
            wrist = self.get_coordinates(landmarks, 'left', 'wrist')

            # Calculate elbow angle
            elbow_angle = self.calculate_angle(shoulder, elbow, wrist)

            # Compute distances between joints
            shoulder2elbow_dist = abs(math.dist(shoulder, elbow))
            shoulder2wrist_dist = abs(math.dist(shoulder, wrist))

            # Press counter logic
            if (elbow_angle > 130) and (shoulder2elbow_dist < shoulder2wrist_dist):
                press_stage = "up"
            if (elbow_angle < 50) and (shoulder2elbow_dist > shoulder2wrist_dist) and (press_stage == 'up'):
                press_stage = 'down'
                press_counter += 1
            curl_stage = None
            squat_stage = None

            # Visualize joint angle
            self.viz_joint_angle(image, elbow_angle, elbow)

        elif current_action == 'squat':
            # Get coords (left side)
            left_shoulder = self.get_coordinates(landmarks, 'left', 'shoulder')
            left_hip = self.get_coordinates(landmarks, 'left', 'hip')
            left_knee = self.get_coordinates(landmarks, 'left', 'knee')
            left_ankle = self.get_coordinates(landmarks, 'left', 'ankle')

            # Get coords (right side)
            right_shoulder = self.get_coordinates(landmarks, 'right', 'shoulder')
            right_hip = self.get_coordinates(landmarks, 'right', 'hip')
            right_knee = self.get_coordinates(landmarks, 'right', 'knee')
            right_ankle = self.get_coordinates(landmarks, 'right', 'ankle')

            # Calculate knee angles
            left_knee_angle = self.calculate_angle(left_hip, left_knee, left_ankle)
            right_knee_angle = self.calculate_angle(right_hip, right_knee, right_ankle)

            # Calculate hip angles
            left_hip_angle = self.calculate_angle(left_shoulder, left_hip, left_knee)
            right_hip_angle = self.calculate_angle(right_shoulder, right_hip, right_knee)

            # Squat counter logic
            thr = 165
            if (left_knee_angle < thr) and (right_knee_angle < thr) and (left_hip_angle < thr) and (right_hip_angle < thr):
                squat_stage = "down"
            if (left_knee_angle > thr) and (right_knee_angle > thr) and (left_hip_angle > thr) and (right_hip_angle > thr) and (squat_stage == 'down'):
                squat_stage = 'up'
                squat_counter += 1
            curl_stage = None
            press_stage = None

            # Visualize joint angles
            self.viz_joint_angle(image, left_knee_angle, left_knee)
            self.viz_joint_angle(image, left_hip_angle, left_hip)

        else:
            pass

        return curl_counter, press_counter, squat_counter

# Global variables for counters and stages
curl_counter = 0
press_counter = 0
squat_counter = 0
curl_stage = None
press_stage = None
squat_stage = None
