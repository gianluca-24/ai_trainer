import math
import cv2
import mediapipe as mp
import numpy as np
import pyttsx3

class PoseDetector:
    def __init__(self, min_detection_confidence=0.5, min_tracking_confidence=0.5):
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence
        self.pose = mp.solutions.pose.Pose(min_detection_confidence=self.min_detection_confidence,
                                           min_tracking_confidence=self.min_tracking_confidence)
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_pose = mp.solutions.pose
        
        # Initialize text-to-speech engine
        self.tts_engine = pyttsx3.init()
        self.tts_engine.setProperty('rate', 130)
        self.tts_engine.setProperty('volume', 0.9)
        
        # Set English voice
        voices = self.tts_engine.getProperty('voices')
        for voice in voices:
            if "english" in voice.name.lower() or "en" in voice.id.lower():
                self.tts_engine.setProperty('voice', voice.id)
                break

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
        cv2.putText(image, str(int(angle)),
                    tuple(np.multiply(joint, [640, 480]).astype(int)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2, cv2.LINE_AA)
        return image

    def speak(self, message):
        """
        Speaks the given message using text-to-speech
        """
        self.tts_engine.say(message)
        self.tts_engine.runAndWait()

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
                return pushup_counter, "⚠️ Please get into pushup position to start"

            # Get coords (left side)
            left_shoulder = self.get_coordinates(landmarks, 'left', 'shoulder') # 11
            left_hip = self.get_coordinates(landmarks, 'left', 'hip') # 23
            left_knee = self.get_coordinates(landmarks, 'left', 'knee') # 25
            left_ankle = self.get_coordinates(landmarks, 'left', 'ankle') # 27
            left_wrist = self.get_coordinates(landmarks, 'left', 'wrist') # 15
            left_elbow = self.get_coordinates(landmarks, 'left', 'elbow') # 13

            # Get coords (right side)
            right_shoulder = self.get_coordinates(landmarks, 'right', 'shoulder') # 12
            right_hip = self.get_coordinates(landmarks, 'right', 'hip') # 24
            right_knee = self.get_coordinates(landmarks, 'right', 'knee') # 26
            right_ankle = self.get_coordinates(landmarks, 'right', 'ankle') # 28
            right_wrist = self.get_coordinates(landmarks, 'right', 'wrist') # 16
            right_elbow = self.get_coordinates(landmarks, 'right', 'elbow') # 14

            wd = abs(math.dist(lw, rw))
            sd = abs(math.dist(ls, rs))
            ed = abs(math.dist(le, re))

            # calculate the angle between elbow, shoulder and wrist, left and right
            left_elbow_angle = self.calculate_angle(left_shoulder, left_elbow, left_wrist)
            right_elbow_angle = self.calculate_angle(right_shoulder, right_elbow, right_wrist)

            # caluclate the angle between shoulder, hip and ankle, left and right
            left_hip_angle = self.calculate_angle(left_shoulder, left_hip, left_ankle)
            right_hip_angle = self.calculate_angle(right_shoulder, right_hip, right_ankle)

            # Calculate knee angles
            left_knee_angle = self.calculate_angle(left_hip, left_knee, left_ankle) 
            right_knee_angle = self.calculate_angle(right_hip, right_knee, right_ankle)

            # Calculate hip angles
            left_hip_angle = self.calculate_angle(left_shoulder, left_hip, left_knee)
            right_hip_angle = self.calculate_angle(right_shoulder, right_hip, right_knee)

            # Shoulder angle: elbow - shoulder - hip
            left_shoulder_angle = self.calculate_angle(left_elbow, left_shoulder, left_hip)
            right_shoulder_angle = self.calculate_angle(right_elbow, right_shoulder, right_hip)
            
            # Check if shoulder distance is similar to wrist distance
            lower_bound_shoulder_wrist = 0.5 * wrist_distance
            upper_bound_shoulder_wrist = 1.5 * wrist_distance

            th_up = 150
            th_down = 120
            
            # logica posizionamento inizio pushup
            if pushup_stage is None:
                if ((lha >= th_up and lka >= th_up) or (rha >= th_up and rka >= th_up)):
                    if lb <= sd <= ub:
                        pushup_stage = 'up'
                        error_message = "You can start pushing up"
                        self.speak(error_message)
                        return pushup_counter, error_message
                    else:
                        if sd < lb:
                            error_message = "⚠️ Shoulders too close to wrists - widen your hand position"
                        elif sd > ub:
                            error_message = "⚠️ Shoulders too far from wrists - bring your hands closer"
                        self.speak(error_message)
                        return pushup_counter, error_message
                else:
                    error_message = "⚠️ Keep your body straight - align your hips!"
                    speak(error_message) 
                    return 0, error_message

               
            # stage up
            if pushup_stage == 'down' and \
                (lower_bound_shoulder_wrist <= shoulder_distance <= upper_bound_shoulder_wrist) and \
                ((left_elbow_angle >= th_up) or (right_elbow_angle >= th_up)):
                pushup_stage = "up" 
                pushup_counter += 1

            if pushup_stage == 'up' and (lea <= th_down or rea <= th_down):
                pushup_stage = "down"

 
            

            # Error handling during exercise (only if not standing)
            if not self.is_standing(landmarks) and (pushup_stage == 'up' or pushup_stage == 'down'):
                error_message = None  

                # Check hip position
                if (left_hip_angle < 160 or right_hip_angle < 160):
                    error_message = "⚠️ Hips too low - raise your hips!"
                elif (lha > 200 or rha > 200):
                    error_message = "⚠️ Hips too high - lower your hips!"

                # Check elbow position
                elif left_shoulder_angle > 100 or right_shoulder_angle > 100:
                    error_message = "⚠️ Arms too wide - keep elbows closer to body"
                elif lsa < 60 or rsa < 60:
                    error_message = "⚠️ Arms too close - widen elbow position slightly"

                # Check hand position
                elif wrist_distance > shoulder_distance * 1.5:
                    error_message = "⚠️ Hands too wide - bring them closer"
                elif wd < sd * 0.5:
                    error_message = "⚠️ Hands too close - widen your grip"
                if error_message:
                    self.speak(error_message)
                    return pushup_counter, error_message

            # Visualize joint angles
            self.viz_joint_angle(image, left_knee_angle, left_knee)
            self.viz_joint_angle(image, left_hip_angle, left_hip)
            self.viz_joint_angle(image, left_elbow_angle, left_elbow)

        return pushup_counter, error_message

# Global variables for counters and stages
pushup_counter = 0
pushup_stage = None
