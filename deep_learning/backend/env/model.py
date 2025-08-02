# import cv2
# import time
# from deepface import DeepFace

# models = [
#   "VGG-Face", 
#   "Facenet", 
#   "Facenet512", 
#   "OpenFace", 
#   "DeepFace", 
#   "DeepID", 
#   "ArcFace", 
#   "Dlib", 
#   "SFace",
#   "GhostFaceNet",
# ]

# metrics = ["cosine", "euclidean", "euclidean_l2"]

# backends = [
#   'opencv', 
#   'ssd', 
#   'dlib', 
#   'mtcnn', 
#   'fastmtcnn',
#   'retinaface', 
#   'mediapipe',
#   'yolov8',
#   'yunet',
#   'centerface',
# ]

# faces = "faces/"  # Path to the folder where face images are stored

# # Initialize the camera
# cap = cv2.VideoCapture(0)

# while cap.isOpened():
#     ret, frame = cap.read()

#     if not ret:
#         print("Failed to grab frame")
#         break

#     # Display the live camera feed
#     cv2.imshow('attendace tracking', frame)

#     # Perform face recognition and emotion analysis
#     try:
#         # DeepFace find
#         dfs = DeepFace.find(
#             img_path=frame,
#             db_path=faces,
#             model_name=models[0],
#             distance_metric=metrics[0],
#             detector_backend=backends[0]
#         )

#         # DeepFace analyze for emotions
#         objs = DeepFace.analyze(
#             img_path=frame,
#             actions=['emotion'],
#         )

#         if len(dfs) > 0:
#             df = dfs[0]
#             obj = objs[0]
#             if not df.empty:
#                 name = df['identity'].values[0].split("/")[-1]
#                 emotion = obj['dominant_emotion']
#                 print(f"Name: {name[:-4]}")
#                 print(f"Emotion: {emotion}")

#     except Exception as e:
#         print(f"Error: {e}")
#         continue

#     # Press ESC to exit
#     if cv2.waitKey(10) & 0xFF == 27:
#         break

# cap.release()
# cv2.destroyAllWindows()




# import cv2
# from deepface import DeepFace
# import streamlit as st
# import os
# from PIL import Image
# import time

# # Streamlit app title and description
# st.title("Attendance Tracking using DeepFace")
# st.text("Live face recognition and emotion detection")

# faces = "faces/"  # Path to the folder where face images are stored

# # Initialize the camera
# cap = cv2.VideoCapture(0)

# # Create a placeholder for video frames and details
# col1, col2 = st.columns(2)  # Split the layout into two columns
# frame_placeholder = col1.empty()  # Camera feed on the left
# details_placeholder = col2.empty()  # Details (name, image, emotion) on the right

# # Set the interval for detection (10 seconds)
# detection_interval = 10
# last_detection_time = time.time()  # Initialize the last detection time

# # Run the loop until the camera is opened
# while cap.isOpened():
#     ret, frame = cap.read()

#     if not ret:
#         st.error("Failed to grab frame from the camera")
#         break

#     # Convert frame to RGB format (from BGR, which OpenCV uses)
#     rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

#     # Display the live camera feed in Streamlit
#     frame_placeholder.image(rgb_frame, channels="RGB")

#     # Check if it's time to perform detection
#     current_time = time.time()
#     if current_time - last_detection_time >= detection_interval:
#         # Perform face recognition and emotion analysis
#         try:
#             # Use default model, metric, and backend for face recognition and emotion analysis
#             dfs = DeepFace.find(
#                 img_path=rgb_frame,
#                 db_path=faces,
#                 model_name="VGG-Face",  # Default model
#                 distance_metric="cosine",  # Default metric
#                 detector_backend="opencv"  # Default backend
#             )

#             # DeepFace analyze (detect emotions)
#             objs = DeepFace.analyze(
#                 img_path=rgb_frame,
#                 actions=['emotion'],
#             )

#             if len(dfs) > 0:
#                 df = dfs[0]
#                 obj = objs[0]
#                 if not df.empty:
#                     # Extract name and dominant emotion
#                     identity_path = df['identity'].values[0]
#                     name = identity_path.split("/")[-1][:-4]  # Remove file extension
#                     emotion = obj['dominant_emotion']

#                     # Display the name and emotion
#                     details_placeholder.write(f"**Name:** {name}")
#                     details_placeholder.write(f"**Emotion:** {emotion}")

#                     # Load the corresponding image from the faces folder
#                     face_image_path = os.path.join(faces, identity_path.split("/")[-1])
#                     if os.path.exists(face_image_path):
#                         face_image = Image.open(face_image_path)
#                         details_placeholder.image(face_image, caption=f"{name}'s Image")
#                 else:
#                     details_placeholder.write("No matching identity found.")
#             else:
#                 details_placeholder.write("No face detected.")

#         except Exception as e:
#             st.error(f"Error: {e}")
        
#         # Update the last detection time
#         last_detection_time = current_time

# # Release the camera when done
# cap.release()
from sklearn.metrics import confusion_matrix
import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt

# Simulating true labels and predicted labels for face recognition with two faces (Face 1 and Face 2)
# True labels: 1 for Face 1, 2 for Face 2
y_true = np.array([1, 1, 2, 2, 1, 1, 2, 2, 1, 2])  # Actual faces
y_pred = np.array([1, 1, 1, 2, 1, 1, 2, 2, 2, 2])  # Predicted faces

# Generate confusion matrix
cm = confusion_matrix(y_true, y_pred)

# Plotting the confusion matrix
plt.figure(figsize=(8, 6))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', cbar=False, 
            xticklabels=['Face 1', 'Face 2'], yticklabels=['Face 1', 'Face 2'])
plt.title('Confusion Matrix for Face Recognition with 2 Faces')
plt.xlabel('Predicted')
plt.ylabel('True')
plt.show()
