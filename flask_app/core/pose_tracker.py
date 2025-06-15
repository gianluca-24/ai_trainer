import math
import cv2
import mediapipe as mp
import numpy as np
import time

# Global variables for counters and stages
pushup_counter = 0
pushup_stage = None

class PoseDetector:
    def __init__(self, min_detection_confidence=0.5, min_tracking_confidence=0.5):
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_pose = mp.solutions.pose
        self.last_message = None
        self.last_message_time = 0

    def process(self, frame_rgb):
        # Create a fresh Pose object per call to avoid timestamp errors
        with self.mp_pose.Pose(
            min_detection_confidence=self.min_detection_confidence,
            min_tracking_confidence=self.min_tracking_confidence
        ) as pose:
            results = pose.process(frame_rgb)
        return results

    def draw_landmarks(self, frame, pose_landmarks):
        self.mp_drawing.draw_landmarks(
            frame, pose_landmarks, self.mp_pose.POSE_CONNECTIONS,
            self.mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
            self.mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=2, circle_radius=2)
        )
        return frame

    def calculate_angle(self, a, b, c):
        a = np.array(a)
        b = np.array(b)
        c = np.array(c)
        radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
        angle = np.abs(radians * 180.0 / np.pi)
        return 360 - angle if angle > 180.0 else angle

    def get_coordinates(self, landmarks, side, joint):
        coord = getattr(self.mp_pose.PoseLandmark, side.upper() + "_" + joint.upper())
        return [landmarks[coord.value].x, landmarks[coord.value].y]

    def viz_joint_angle(self, image, angle, joint):
        cv2.putText(
            image, str(int(angle)),
            tuple(np.multiply(joint, [image.shape[1], image.shape[0]]).astype(int)),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2, cv2.LINE_AA
        )
        return image

    def is_standing(self, landmarks):
        ls_y = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value].y
        rs_y = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y
        lh_y = landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value].y
        rh_y = landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP.value].y
        la_y = landmarks[self.mp_pose.PoseLandmark.LEFT_ANKLE.value].y
        ra_y = landmarks[self.mp_pose.PoseLandmark.RIGHT_ANKLE.value].y
        shoulder_y = (ls_y + rs_y) / 2
        hip_y = (lh_y + rh_y) / 2
        ankle_y = (la_y + ra_y) / 2
        return (hip_y - shoulder_y) > 0.15 and (ankle_y - hip_y) > 0.15

    def count_reps(self, image, current_action, landmarks):
        global pushup_counter, pushup_stage
        error_message = None

        if current_action == 'pushup':
            if self.is_standing(landmarks):
                pushup_stage = None
                pushup_counter = 0
                return pushup_counter, "Please get into pushup position to start"

            ls = self.get_coordinates(landmarks, 'left', 'shoulder')
            lh = self.get_coordinates(landmarks, 'left', 'hip')
            lk = self.get_coordinates(landmarks, 'left', 'knee')
            la = self.get_coordinates(landmarks, 'left', 'ankle')
            lw = self.get_coordinates(landmarks, 'left', 'wrist')
            le = self.get_coordinates(landmarks, 'left', 'elbow')
            rs = self.get_coordinates(landmarks, 'right', 'shoulder')
            rh = self.get_coordinates(landmarks, 'right', 'hip')
            rk = self.get_coordinates(landmarks, 'right', 'knee')
            ra = self.get_coordinates(landmarks, 'right', 'ankle')
            rw = self.get_coordinates(landmarks, 'right', 'wrist')
            re = self.get_coordinates(landmarks, 'right', 'elbow')

            wd = abs(math.dist(lw, rw))
            sd = abs(math.dist(ls, rs))
            lea = self.calculate_angle(ls, le, lw)
            rea = self.calculate_angle(rs, re, rw)
            lha = self.calculate_angle(ls, lh, lk)
            rha = self.calculate_angle(rs, rh, rk)
            lka = self.calculate_angle(lh, lk, la)
            rka = self.calculate_angle(rh, rk, ra)
            lsa = self.calculate_angle(le, ls, lh)
            rsa = self.calculate_angle(re, rs, rh)

            lb, ub = 0.5 * wd, 1.5 * wd
            th_up, th_down = 150, 120

            if pushup_stage is None:
                if ((lha >= th_up and lka >= th_up) or (rha >= th_up and rka >= th_up)):
                    if lb <= sd <= ub:
                        pushup_stage = 'up'
                        return pushup_counter, "You can start pushing up"
                    else:
                        if sd < lb:
                            error_message = "Shoulders too close to wrists - widen your hand position"
                        elif sd > ub:
                            error_message = "Shoulders too far from wrists - bring your hands closer"
                        return pushup_counter, error_message
                else:
                    error_message = "Keep your body straight - align your hips!"
                    return pushup_counter, error_message

            if pushup_stage == 'down' and lb <= sd <= ub and (lea >= th_up or rea >= th_up):
                pushup_stage = "up"
                pushup_counter += 1

            if pushup_stage == 'up' and (lea <= th_down or rea <= th_down):
                pushup_stage = "down"

            if not self.is_standing(landmarks) and pushup_stage in ['up', 'down']:
                if (lha < 160 or rha < 160):
                    error_message = "Hips too low - raise your hips!"
                elif (lha > 200 or rha > 200):
                    error_message = "Hips too high - lower your hips!"
                elif lsa > 100 or rsa > 100:
                    error_message = "Arms too wide - keep elbows closer to body"
                elif lsa < 60 or rsa < 60:
                    error_message = "Arms too close - widen elbow position slightly"
                elif wd > sd * 1.5:
                    error_message = "Hands too wide - bring them closer"
                elif wd < sd * 0.5:
                    error_message = "Hands too close - widen your grip"
                if error_message:
                    return pushup_counter, error_message

            self.viz_joint_angle(image, lka, lk)
            self.viz_joint_angle(image, lha, lh)
            self.viz_joint_angle(image, lea, le)

        return pushup_counter, None

    def should_speak(self, message, delay=5):
        current_time = time.time()
        if self.last_message is None:
            self.last_message = message
            self.last_message_time = current_time
            return True
        if message != self.last_message or (current_time - self.last_message_time > delay):
            self.last_message = message
            self.last_message_time = current_time
            return True
        return False
