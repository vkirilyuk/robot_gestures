import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

import numpy as np
import cv2 as cv
import time

import os
from spot_controller import SpotController
script_dir = os.path.dirname(__file__)
task_path = os.path.join(script_dir, 'gesture_recognizer.task')

ROBOT_IP = "192.168.50.3"#os.environ['ROBOT_IP']
SPOT_USERNAME = "admin"#os.environ['SPOT_USERNAME']
SPOT_PASSWORD = "2zqa8dgw7lor"#os.environ['SPOT_PASSWORD']

last_gesture = None
consecutive_gestures = 0

def main():
  # Use wrapper in context manager to lease control, turn on E-Stop, power on the robot and stand up at start
  # and to return lease + sit down at the end
  with SpotController(username=SPOT_USERNAME, password=SPOT_PASSWORD, robot_ip=ROBOT_IP) as spot:

    # time.sleep(2)

    # # Move head to specified positions with intermediate time.sleep
    # spot.move_head_in_points(yaws=[0.2, 0],
    #                           pitches=[0.3, 0],
    #                           rolls=[0.4, 0],
    #                           sleep_after_point_reached=1)
    # time.sleep(3)

    # # Make Spot to move by goal_x meters forward and goal_y meters left
    # spot.move_to_goal(goal_x=0.5, goal_y=0)
    # time.sleep(3)

    # # Control Spot by velocity in m/s (or in rad/s for rotation)
    # spot.move_by_velocity_control(v_x=-0.3, v_y=0, v_rot=0, cmd_duration=2)
    # time.sleep(3)

    BaseOptions = mp.tasks.BaseOptions
    GestureRecognizer = mp.tasks.vision.GestureRecognizer
    GestureRecognizerOptions = mp.tasks.vision.GestureRecognizerOptions
    GestureRecognizerResult = mp.tasks.vision.GestureRecognizerResult
    VisionRunningMode = mp.tasks.vision.RunningMode

    # Create a gesture recognizer instance with the live stream mode:
    def print_result(result: GestureRecognizerResult, output_image: mp.Image, timestamp_ms: int):
        global last_gesture
        global consecutive_gestures
        if result.gestures:
          print('result:', [g[0].category_name for g in result.gestures])
          top_gesture = result.gestures[0][0]
          name = top_gesture.category_name
          if last_gesture == name:
            consecutive_gestures += 1
            if consecutive_gestures == 10:
              print('*' * 60)
              print('*' * 30, name, '*' * 30)
              print('*' * 60)
              if last_gesture == 'Thumb_Up':
                spot.bow(pitch=-0.5, body_height=0.5, sleep_after_point_reached=1)
                pass
              elif last_gesture == 'Victory':
                exit()
                pass
          else:
            last_gesture = name
            consecutive_gestures = 1
        else:
          last_gesture = None
          consecutive_gestures = 0

    options = GestureRecognizerOptions(
        base_options=BaseOptions(model_asset_path=task_path),
        running_mode=VisionRunningMode.LIVE_STREAM,
        result_callback=print_result)

    started = time.time()

    with GestureRecognizer.create_from_options(options) as recognizer:

      cap = cv.VideoCapture(0)
      if not cap.isOpened():
          print("Cannot open camera")
          exit()

      while True:
        if time.time() - started > 120:
          exit()
        # Capture frame-by-frame
        ret, frame = cap.read()
        # if frame is read correctly ret is True
        if not ret:
            print("Can't receive frame (stream end?). Exiting ...")
            break
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
        recognizer.recognize_async(mp_image, time.time())

  cap.release()

if __name__ == '__main__':
  main()
