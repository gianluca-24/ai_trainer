# ai_trainer
ai_trainer is an app developed to help people improve their push-up technique. We chose push-ups because they are a common exercise that many people perform incorrectly.
The app works on both PC and smartphone.
All you need is a camera, a microphone, and enough space to do the exercises.

We use the MediaPipe model to recognize skeletal joints from live video. By analyzing the positions of these joints, we evaluate distances and angles, and set thresholds for common mistakes in the exercise. When you make an error, the app provides real-time feedback, helping you correct your form during the workout.
The app is fully "hands-free"—after starting, you can control everything with voice commands.
There is also a scoring feature and an exercise history, so you can track your progress over time.

# How to Run It

## For PC

1. Install the requirements.
2. Open the command line.
3. Navigate to the folder containing the Flask app.
   - **For Windows users:**  
     Run: `python app.py --port=5050`
   - **For Mac users:**  
     Run: `python app.py --port=5050`
4. Copy the generated link from the terminal and open it in your browser.

## For Smartphone

1. Install the `ngrok` package.
2. In your terminal, run:  
   `ngrok config add-authtoken <your_token>`
3. Run the `run_app.ssh` script.
4. In a different terminal, run:  
   `ngrok http 5050`
5. Click on the generated link or copy it into your phone's browser (note: does not work with Safari).

# How to Use the App

1. Log in.
2. Read the disclaimer, which explains how to use voice commands.
3. Set up your workout.
4. During rest periods, The App will check how you're going and adjust the workout

