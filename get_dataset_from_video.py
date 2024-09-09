import cv2
import os

# video_path = 'video/part1.mp4'
# video_path = 'video/part2.mp4'
video_path = 'video/part1.mp4'
output_dir = 'dataset'
os.makedirs(output_dir, exist_ok=True)


cap = cv2.VideoCapture(video_path)
if not cap.isOpened():
    print("Error: Could not open video.")
    exit()

frame_count = 0
saved_count = 0

while True:
    ret, frame = cap.read()

    if not ret:
        break

    if frame_count % 200 == 0:
        frame_filename = os.path.join(output_dir, f'frame_{saved_count}.jpg')
        cv2.imwrite(frame_filename, frame)
        saved_count += 1
        print(f"Saved {frame_filename}")

    frame_count += 1

cap.release()
print(f"Total frames saved: {saved_count}")
