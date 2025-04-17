import cv2
import os
import time
import requests
import math
from datetime import datetime
from email.message import EmailMessage
from ultralytics import YOLO
from django.conf import settings
import django
import sys
from ultralytics.utils.plotting import Annotator

# Django setup
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_waste_management_project.settings')
django.setup()

from swm_app.models import CleaningTask, CleaningCrew
from django.core.mail import EmailMultiAlternatives

# Paths & Configs
IP_CAM_URL = 'http://192.0.0.4:8080/video'
MODEL_PATH_1 = 'C:/Users/nilesh/Smart_Waste_Management/swm_app/models/best_garbage.pt'
MODEL_PATH_2 = 'C:/Users/nilesh/Smart_Waste_Management/swm_app/models/best_Spills.pt'
SNAPSHOT_DIR = 'media/detections'
os.makedirs(SNAPSHOT_DIR, exist_ok=True)

# Load Models
model_garbage = YOLO(MODEL_PATH_1)
model_spill = YOLO(MODEL_PATH_2)

# Cooldown
ALERT_DELAY = 5 * 60  # 5 minutes
last_alert_time = 0

def haversine(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 6371.0 * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def get_current_location():
    try:
        data = requests.get("https://ipinfo.io/json").json()
        lat, lon = map(float, data.get("loc", "").split(","))
        return lat, lon
    except:
        return None, None

def find_nearest_crew(lat, lon):
    crews = CleaningCrew.objects.filter(availability_status=True, verified=True,
                                         current_latitude__isnull=False, current_longitude__isnull=False)
    min_dist = float('inf')
    nearest = None
    for crew in crews:
        dist = haversine(lat, lon, float(crew.current_latitude), float(crew.current_longitude))
        if dist < min_dist:
            min_dist, nearest = dist, crew
    return nearest

def send_email_with_image(snapshot_path, location_link, timestamp, crew=None):
    subject = "🚨 Garbage/Spill Detected"
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = [crew.email] if crew else ["nkale882@gmail.com"]
    name = crew.full_name if crew else "Admin"

    text = f"""Hello {name},

A garbage or spill incident has been detected.

📍 Location: {location_link}
🕒 Time: {timestamp}

{"Please take action immediately." if crew else "No crew was available to assign this task."}
"""

    html = f"""<html><body>
    <h2>🚨 {'Task Assigned' if crew else 'No Available Crew'}: Garbage/Spill Detected</h2>
    <p>Hello <strong>{name}</strong>,</p>
    <p>A detection was made:</p>
    <p><strong>📍 Location:</strong> <a href="{location_link}">View Map</a><br>
    <strong>🕒 Time:</strong> {timestamp}</p>
    <p>{'Please resolve this task as soon as possible.' if crew else 'Please assign crew manually.'}</p>
    </body></html>"""

    msg = EmailMultiAlternatives(subject, text, from_email, to_email)
    msg.attach_alternative(html, "text/html")

    if os.path.exists(snapshot_path):
        with open(snapshot_path, "rb") as f:
            msg.attach(os.path.basename(snapshot_path), f.read(), "image/jpeg")

    msg.send()

# Video Stream
cap = cv2.VideoCapture(IP_CAM_URL)
lat, lon = get_current_location()
location_link = f"https://www.google.com/maps?q={lat},{lon}"

print("🚀 Detection Started...")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    current_time = time.time()
    if current_time - last_alert_time < ALERT_DELAY:
        continue

    detected = False
    detection_type = None
    all_results = []

    for model, label in [(model_garbage, "garbage"), (model_spill, "spill")]:
        result = model.predict(source=frame, save=False, verbose=False)[0]
        if result.boxes:
            all_results.append((label, result))
            detected = True
            detection_type = label
            break

    if detected:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"{detection_type}_{timestamp}.jpg"
        filepath = os.path.join(SNAPSHOT_DIR, filename)

        # Annotate image
        result = all_results[0][1]
        annotator = Annotator(frame.copy())
        for box in result.boxes:
            annotator.box_label(box.xyxy[0], label=detection_type, color=(255, 0, 0))
        labeled_img = annotator.result()
        cv2.imwrite(filepath, labeled_img)

        # Assign task
        crew = find_nearest_crew(lat, lon)
        task = CleaningTask.objects.create(
            location=location_link,
            snapshot=f"detections/{filename}",
            description="Detected via CCTV",
            assigned_to=crew,
            status="assigned" if crew else "pending"
        )

        print(f"✅ {detection_type.capitalize()} detected. Task created for: {crew.full_name if crew else 'Admin'}")
        send_email_with_image(filepath, location_link, timestamp, crew)
        last_alert_time = current_time

    cv2.imshow("Smart Waste Detection", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
