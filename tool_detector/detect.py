import cv2
from ultralytics import YOLO
import pandas as pd
from collections import Counter
import numpy as np  # Added for average calculation
import os
from models import db, Detection
from flask_login import current_user

class ToolDetector:
    def __init__(self, model_path, class_names):
        self.model = YOLO(model_path)
        self.class_names = class_names

    def detect_and_count(self, frame):
        results = self.model(frame)[0]  # Run inference on the frame
        detections = results.boxes.cls.cpu().numpy()  # Get class indices of detections
        confs = results.boxes.conf.cpu().numpy()  # Get confidence scores
        count = Counter(detections)  # Count occurrences per class
        #class_counts = {class_names[int(cls)]: count.get(cls, 0) for cls in range(len(class_names))}
        class_counts = {self.class_names[int(cls)]: 1 if cls in count else 0 for cls in range(len(self.class_names))}

        # Calculate total objects detected (sum of all class counts)
        total = sum(class_counts.values())
        class_counts['total'] = total

        return class_counts

    def process_video(self, video_path):
        
        output_excel = 'demo/result.xlsx'  # output

        # Process the video
        cap = cv2.VideoCapture(video_path)
        resW, resH= 1280, 720 # Width, Height
  
        ret = cap.set(cv2.CAP_PROP_FRAME_WIDTH, resW) 
        ret = cap.set(cv2.CAP_PROP_FRAME_HEIGHT, resH) 

        fps = cap.get(cv2.CAP_PROP_FPS)  # Get frames per second

        if not fps or fps <= 0:
            raise ValueError("Could not retrieve FPS from video.")

        # Set bounding box colors
        bbox_colors = [(164,120,87), (68,148,228), (93,97,209), (178,182,133), (88,159,106), 
                    (96,202,231), (159,124,168), (169,162,241), (98,118,150), (172,176,184)]

        frame_counts = []
        frame_num = 0
        df = pd.DataFrame()

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.resize(frame,(resW,resH))
        
            results = self.model(frame, verbose=False)[0]

            counts = self.detect_and_count(frame)

            frame_counts.append(counts)
            frame_num += 1
            
            # Draw bounding boxes
            for box, cls, conf in zip(results.boxes.xyxy, results.boxes.cls, results.boxes.conf):
                x1, y1, x2, y2 = map(int, box)
                color = bbox_colors[int(cls) % len(bbox_colors)]
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(frame, f"{self.class_names[int(cls)]} {conf:.2f}",
                            (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

            # Show the video frame in a window
            window_name ="Tool Detection"
            cv2.imshow(window_name, frame)
            key = cv2.waitKey(5)
            if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                break
            elif key == ord('q') or key == ord('Q'): # Press 'q' to quit
                break
            elif key == ord('s') or key == ord('S'): # Press 's' to pause inference
                cv2.waitKey()
                
        cap.release()
        cv2.destroyAllWindows()

        # Only display the last result
        if frame_counts:  # make sure we actually have results
            last_result = frame_counts[-1]   # take the last frame's counts
            df = pd.DataFrame([last_result]) # wrap in list so DataFrame builds one row
            df.to_excel(output_excel, index=False)

            # Save each frame’s detections into DB
            for _, row in df.iterrows():
                detection = Detection(
                    login_id=str(current_user.id),
                    drill=int(row.get("drill", 0)),
                    hammer=int(row.get("hammer", 0)),
                    pliers=int(row.get("pliers", 0)),
                    scissors=int(row.get("scissors", 0)),
                    screwdriver=int(row.get("screwdriver", 0)),
                    tape_measure=int(row.get("tape-measure", 0)),  # rename column in df if needed
                    wrench=int(row.get("wrench", 0))
                )
                db.session.add(detection)

            db.session.commit()

            print(f"Last frame counts exported to {output_excel}")
        else:
            print("No detections found, nothing to export.")

        return df