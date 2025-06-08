# app/core/pose_tracker.py
import math
import cv2
import mediapipe as mp
import numpy as np
import pyttsx3

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
    # Initialize text-to-speech engine
    tts_engine = pyttsx3.init()
    tts_engine.setProperty('rate', 130)
    tts_engine.setProperty('volume', 0.9)

    voices = engine.getProperty('voices')
    for voice in voices:
        if "english" in voice.name.lower() or "en" in voice.id.lower():
            engine.setProperty('voice', voice.id)
            break

    
    def speak(message):
        tts_engine.say(message)
        tts_engine.runAndWait()

    def is_standing(self, landmarks):
        """
        Determines if the person is standing by checking relative y-coordinates of body parts.
        Returns True if standing, False if in pushup position or other pose.
        """
        # Get y coordinates of key points
        left_shoulder_y = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value].y
        right_shoulder_y = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y
        left_hip_y = landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value].y
        right_hip_y = landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP.value].y
        left_ankle_y = landmarks[self.mp_pose.PoseLandmark.LEFT_ANKLE.value].y
        right_ankle_y = landmarks[self.mp_pose.PoseLandmark.RIGHT_ANKLE.value].y

        # Calculate average y positions
        shoulder_y = (left_shoulder_y + right_shoulder_y) / 2
        hip_y = (left_hip_y + right_hip_y) / 2
        ankle_y = (left_ankle_y + right_ankle_y) / 2

        # In standing position:
        # 1. Shoulders should be significantly higher than hips (smaller y value)
        # 2. Hips should be significantly higher than ankles
        # 3. The differences should be substantial (using 0.15 as threshold)
        shoulder_to_hip_diff = hip_y - shoulder_y
        hip_to_ankle_diff = ankle_y - hip_y

        return shoulder_to_hip_diff > 0.15 and hip_to_ankle_diff > 0.15

    def count_reps(self, image, current_action, landmarks):
        """
        Counts repetitions of each exercise. Global count and stage (i.e., state) variables are updated within this function.
        Returns a tuple of (counter, error_message) where error_message is None if no errors are detected
        """
        global pushup_counter, pushup_stage
        error_message = None


        if current_action == 'pushup':
            # First check if person is standing
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

            # calculate the distance between the wrists
            wrist_distance = abs(math.dist(left_wrist, right_wrist))            
            # calculate the distance between shoulders
            shoulder_distance = abs(math.dist(left_shoulder, right_shoulder))
            # calculate the distance between elbows
            elbow_distance = abs(math.dist(left_elbow, right_elbow))

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
            
            # Check if shoulder distance is similar to wrist distance (within 0.95-1.05 range)
            lower_bound_shoulder_wrist = 0.5 * wrist_distance
            upper_bound_shoulder_wrist = 1.5 * wrist_distance

            th_up = 150
            th_down = 120
            # logica posizionamento inizio pushup
            if pushup_stage is None:
                if ((left_hip_angle >= th_up) and (left_knee_angle >= th_up)) or \
                ((right_hip_angle >= th_up) and (right_knee_angle >= th_up)):

                    if lower_bound_shoulder_wrist <= shoulder_distance <= upper_bound_shoulder_wrist:
                        pushup_stage = 'up'
                        speak("You can start pushing up") 
                        return 0, "You can start pushing up"

                    else:
                        if shoulder_distance < lower_bound_shoulder_wrist:
                            error_message = "⚠️ Shoulders too close to wrists - widen your hand position"
                        elif shoulder_distance > upper_bound_shoulder_wrist:
                            error_message = "⚠️ Shoulders too far from wrists - bring your hands closer"
                        speak(error_message) 
                        return 0, error_message

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

            # stage down
            if pushup_stage == 'up' and \
                ((left_elbow_angle <= th_down) or (right_elbow_angle <= th_down)):
                pushup_stage = "down"

 
            

            # Error handling during exercise (only if not standing)
            if not self.is_standing(landmarks) and (pushup_stage == 'up' or pushup_stage == 'down'):
                error_message = None  

                # Check hip position
                if (left_hip_angle < 160 or right_hip_angle < 160):
                    error_message = "⚠️ Hips too low - raise your hips!"
                elif (left_hip_angle > 200 or right_hip_angle > 200):
                    error_message = "⚠️ Hips too high - lower your hips!"

                # Check elbow position
                elif left_shoulder_angle > 100 or right_shoulder_angle > 100:
                    error_message = "⚠️ Arms too wide - keep elbows closer to body"
                elif left_shoulder_angle < 60 or right_shoulder_angle < 60:
                    error_message = "⚠️ Arms too close - widen elbow position slightly"

                # Check hand position
                elif wrist_distance > shoulder_distance * 1.5:
                    error_message = "⚠️ Hands too wide - bring them closer"
                elif wrist_distance < shoulder_distance * 0.5:
                    error_message = "⚠️ Hands too close - widen your grip"

                if error_message:
                    speak(error_message)
                    return 0, error_message





            # Visualize joint angles
            self.viz_joint_angle(image, left_knee_angle, left_knee)
            self.viz_joint_angle(image, left_hip_angle, left_hip)
            self.viz_joint_angle(image, left_elbow_angle, left_elbow)

        return pushup_counter, error_message

# Global variables for counters and stages
pushup_counter = 0
pushup_stage = None





        # if current_action == 'curl':
        #     # Get coords
        #     shoulder = self.get_coordinates(landmarks, 'left', 'shoulder')
        #     elbow = self.get_coordinates(landmarks, 'left', 'elbow')
        #     wrist = self.get_coordinates(landmarks, 'left', 'wrist')

        #     # Calculate elbow angle
        #     angle = self.calculate_angle(shoulder, elbow, wrist)

        #     # Curl counter logic
        #     if angle < 30:
        #         curl_stage = "up"
        #     if angle > 140 and curl_stage == 'up':
        #         curl_stage = "down"
        #         curl_counter += 1
        #     press_stage = None
        #     squat_stage = None

        #     # Visualize joint angle
        #     self.viz_joint_angle(image, angle, elbow)

        # elif current_action == 'press':
        #     # Get coords
        #     shoulder = self.get_coordinates(landmarks, 'left', 'shoulder')
        #     elbow = self.get_coordinates(landmarks, 'left', 'elbow')
        #     wrist = self.get_coordinates(landmarks, 'left', 'wrist')

        #     # Calculate elbow angle
        #     elbow_angle = self.calculate_angle(shoulder, elbow, wrist)

        #     # Compute distances between joints
        #     shoulder2elbow_dist = abs(math.dist(shoulder, elbow))
        #     shoulder2wrist_dist = abs(math.dist(shoulder, wrist))

        #     # Press counter logic
        #     if (elbow_angle > 130) and (shoulder2elbow_dist < shoulder2wrist_dist):
        #         press_stage = "up"
        #     if (elbow_angle < 50) and (shoulder2elbow_dist > shoulder2wrist_dist) and (press_stage == 'up'):
        #         press_stage = 'down'
        #         press_counter += 1
        #     curl_stage = None
        #     squat_stage = None

        #     # Visualize joint angle
        #     self.viz_joint_angle(image, elbow_angle, elbow)




                