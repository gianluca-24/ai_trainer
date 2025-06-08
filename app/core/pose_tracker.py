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
        global pushup_counter, pushup_stage

        if current_action == 'pushup':
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

            # CHECK POSITIONS 
            # # Squat counter logic
            # thr = 165
            # if (left_knee_angle < thr) and (right_knee_angle < thr) and (left_hip_angle < thr) and (right_hip_angle < thr):
            #     squat_stage = "down"
            # if (left_knee_angle > thr) and (right_knee_angle > thr) and (left_hip_angle > thr) and (right_hip_angle > thr) and (squat_stage == 'down'):
            #     squat_stage = 'up'
            #     squat_counter += 1
            
            # Check if shoulder distance is similar to wrist distance (within 0.95-1.05 range)
            lower_bound_shoulder_wrist = 0.6 * wrist_distance
            upper_bound_shoulder_wrist = 1.4 * wrist_distance

            th_up = 150
            th_down = 120
            error = 0
        # da aggiungere un controllo per vedere se l'utente è in piedi o sdraiato
        

            # if standing: # check con comandi vocali or counter or bohhhh
            #     pushup_stage = None

            # logica posizionamento inizio pushup
            if pushup_stage == None:
                if  (left_hip_angle >= th_up) and (right_hip_angle >= th_up) and \
                (left_knee_angle >= th_up) and (right_knee_angle >= th_up):
                    print('stai in posizione con il bacino')
                    if (lower_bound_shoulder_wrist <= shoulder_distance <= upper_bound_shoulder_wrist):
                        print('spalle e polsi sono allineati')
                        print('inizio pushup')
                        pushup_stage = 'up'
                        print('bravo 6 apppppp!!!!')

                    else:
                        print('spalle e polsi NON sono allineati')
                        if shoulder_distance < lower_bound_shoulder_wrist:
                            print('spalle troppo vicine ai polsi')
                        elif shoulder_distance > upper_bound_shoulder_wrist:
                            print('spalle troppo lontane dai polsi')

                else:
                    print('raddrizza sto culo!!!!')
                # check positioning
                #
                #<|diff_marker|>#
                #
               
            # stage up


            if pushup_stage == 'down' and (lower_bound_shoulder_wrist <= shoulder_distance <= upper_bound_shoulder_wrist) and \
                (left_elbow_angle >= th_up) and (right_elbow_angle >= th_up):
                # Shoulders and wrists are aligned within the specified range
                pushup_stage = "up" 
                pushup_counter += 1
                print('ancora una uomo!!!!!!!!!!')

            # to add the angle between elbow, shoulder and hip to check if the elbows are in the right position (30 gradi,60 gradi)

            # stage down
            if pushup_stage == 'up' and \
                (left_elbow_angle <= th_down) and (right_elbow_angle <= th_down):
                pushup_stage = "down"
                print('bravo 6 daun!!!')


            #########################################################
            # ERRORS HANDLING
            #########################################################
            #########################################################
            #########################################################

            # if pushup_stage == None:
            #     print('non hai iniziato il pushup')
            #     pass

            # errors while going down
            if pushup_stage == 'up' or pushup_stage == 'down':
                # 1. bacino troppo basso o alto
                if (left_hip_angle < 160 or right_hip_angle < 160):
                    print("Errore: Il bacino è troppo basso, alzalo!")
                elif (left_hip_angle > 200 or right_hip_angle > 200):
                    print("Errore: Il bacino è troppo alto, abbassalo!")

                # 2. gomiti troppo larghi (shoulder angle)
                if left_shoulder_angle > 100 or right_shoulder_angle > 100:
                    print("Arms are spread wide or lifted")
                elif left_shoulder_angle < 60 or right_shoulder_angle < 60:
                    print("Arms are close to body")

                # 3. mani troppo larghe o troppo vicine
                if wrist_distance > shoulder_distance * 1.5:
                    print("Errore: Le mani sono troppo larghe! Avvicinale un po'.")
                elif wrist_distance < shoulder_distance * 0.5:
                    print("Errore: Le mani sono troppo vicine! Allargale un po'.")

            # if pushup_stage == 'down':
            #     pass


                
            # Visualize joint angles
            self.viz_joint_angle(image, left_knee_angle, left_knee)
            self.viz_joint_angle(image, left_hip_angle, left_hip)
            self.viz_joint_angle(image, left_elbow_angle, left_elbow)

        else:
            pass

        return pushup_counter

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




                