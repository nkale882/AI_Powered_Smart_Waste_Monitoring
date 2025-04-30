import cv2
import os
import time
import requests
import math
from datetime import datetime
from email.message import EmailMessage
from datetime import datetime
from ultralytics import YOLO
from django.conf import settings
import django
import sys
from ultralytics.utils.plotting import Annotator


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_waste_management_project.settings')
django.setup()

from swm_app.models import CleaningTask, CleaningCrew

from django.core.mail import EmailMultiAlternatives

def send_detection_alert_email(snapshot_path, location_link, timestamp, crew):
    subject = "🚨 Task Assigned: Garbage/Spill Detected"
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = [crew.email]

    text_content = f"""
    Hello {crew.full_name},

    You have been assigned a new cleaning task.

    📍 Location: {location_link}
    🕒 Time: {timestamp}

    Please take action immediately.
    """

    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f9f9f9; padding: 20px;">
      <div style="background-color: #ffffff; padding: 20px; border-radius: 10px; border: 1px solid #ddd; max-width: 600px; margin: auto;">
        <h2 style="color: #e67e22;">🧹 New Cleaning Task Assigned</h2>
        <p style="font-size: 16px; color: #333;">Hello <strong>{crew.full_name}</strong>,</p>
        <p style="font-size: 16px; color: #333;">A garbage or spill incident has been detected and assigned to you.</p>
        <p style="font-size: 16px; color: #333;"><strong>📍 Location:</strong> <a href="{location_link}" style="color: #2980b9;">View on Map</a></p>
        <p style="font-size: 16px; color: #333;"><strong>🕒 Time:</strong> {timestamp}</p>
        <br>
        <p style="font-size: 14px; color: #555;">Please resolve this task as soon as possible.</p>
        <p style="font-size: 14px; color: #555;">– Smart Waste Management System</p>
      </div>
    </body>
    </html>
    """

    msg = EmailMultiAlternatives(subject, text_content, from_email, to_email)
    msg.attach_alternative(html_content, "text/html")

    # Attach snapshot if available
    if os.path.exists(snapshot_path):
        try:
            with open(snapshot_path, "rb") as f:
                msg.attach(os.path.basename(snapshot_path), f.read(), "image/jpeg")
            print(f"✅ Snapshot attached successfully: {snapshot_path}")
        except Exception as e:
            print(f"❌ Failed to attach snapshot: {e}")

    msg.send()

def send_admin_alert_email(snapshot_path, location_link, timestamp):
    subject = "🚨 No Available Crew: Garbage/Spill Detected"
    from_email = settings.DEFAULT_FROM_EMAIL
    admin_email = "gmail.com"  # Replace with actual admin email

    text_content = f"""
    Hello Admin,

    A garbage or spill incident has been detected, but no available crew could be assigned.

    📍 Location: {location_link}
    🕒 Time: {timestamp}

    Please review the situation and assign a crew manually if needed.
    """

    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f9f9f9; padding: 20px;">
      <div style="background-color: #ffffff; padding: 20px; border-radius: 10px; border: 1px solid #ddd; max-width: 600px; margin: auto;">
        <h2 style="color: #e67e22;">🚨 No Available Crew: Garbage/Spill Detected</h2>
        <p style="font-size: 16px; color: #333;">Hello Admin,</p>
        <p style="font-size: 16px; color: #333;">A garbage or spill incident has been detected, but no crew was available to take action.</p>
        <p style="font-size: 16px; color: #333;"><strong>📍 Location:</strong> <a href="{location_link}" style="color: #2980b9;">View on Map</a></p>
        <p style="font-size: 16px; color: #333;"><strong>🕒 Time:</strong> {timestamp}</p>
        <br>
        <p style="font-size: 14px; color: #555;">Please review the situation and assign a crew manually if needed.</p>
        <p style="font-size: 14px; color: #555;">– Smart Waste Management System</p>q
      </div>
    </body>
    </html>
    """

    msg = EmailMultiAlternatives(subject, text_content, from_email, [admin_email])
    msg.attach_alternative(html_content, "text/html")

    # Attach snapshot if available
    if os.path.exists(snapshot_path):
        try:
            with open(snapshot_path, "rb") as f:
                msg.attach(os.path.basename(snapshot_path), f.read(), "image/jpeg")
            print(f"✅ Snapshot attached successfully: {snapshot_path}")
        except Exception as e:
            print(f"❌ Failed to attach snapshot: {e}")

    # Send email
    try:
        msg.send()
        print("✅ Email sent successfully.")
    except Exception as e:
        print(f"❌ Error sending email: {e}")


def haversine(lat1, lon1, lat2, lon2):
    # Convert degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    # Radius of the Earth in km
    radius = 6371.0
    distance = radius * c

    return distance

# ------------------- Function to Fetch Current Location ------------------- #
def get_current_location():
    try:
        response = requests.get("https://ipinfo.io/json")
        data = response.json()
        loc = data.get("loc", "")
        lat, lon = map(float, loc.split(","))
        return lat, lon
    except Exception as e:
        print("❌ Error fetching location:", e)
        return None, None

# ------------------- Find Nearest Crew ------------------- #
def find_nearest_crew(lat, lon):
    crews = CleaningCrew.objects.filter(availability_status=True,verified=True, current_latitude__isnull=False, current_longitude__isnull=False)
    nearest_crew = None
    min_distance = float('inf')

    for crew in crews:
        crew_coords = (float(crew.current_latitude), float(crew.current_longitude))
        device_coords = (lat, lon)
        distance = haversine(device_coords[0], device_coords[1], crew_coords[0], crew_coords[1])

        if distance < min_distance:
            min_distance = distance
            nearest_crew = crew

    return nearest_crew

garbage_model = YOLO("C:/Users/nilesh/Downloads/best_garbage.pt")
spill_model = YOLO("C:/Users/nilesh/Downloads/best_Spills.pt")

# --- Detection Threshold ---
DETECTION_THRESHOLD = 0.5 

# Set the time delay for the next alert (in seconds)
alert_delay = 5 * 60  # 5 minutes
last_alert_time = 0
# ------------------- Main Detection Logic ------------------- #
cap = cv2.VideoCapture(0)
lat, lon = get_current_location()
location_link = f"https://www.google.com/maps?q={lat},{lon}"

print("📍 Device Location:", location_link)
print("🚀 Detection started. Press 'q' to quit.")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break


    current_time = time.time()
    if current_time - last_alert_time < 300:
        # Not enough time has passed; skip detection
        cv2.imshow("Smart Waste Detection", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
        continue

    garbage_results = garbage_model.predict(source=frame, save=False, verbose=False)
    spill_results = spill_model.predict(source=frame, save=False, verbose=False)

    detected = False
    frame_copy = frame.copy()
    annotator = Annotator(frame_copy)

    for box in garbage_results[0].boxes:
        conf = float(box.conf[0])
        cls_name = garbage_model.names[int(box.cls[0])]
        if conf >= DETECTION_THRESHOLD:
            annotator.box_label(box.xyxy[0], label=f"{cls_name} ({conf:.2f})", color=(0, 255, 0))
            detected = True

    for box in spill_results[0].boxes:
        conf = float(box.conf[0])
        cls_name = spill_model.names[int(box.cls[0])]
        if conf >= DETECTION_THRESHOLD:
            annotator.box_label(box.xyxy[0], label=f"{cls_name} ({conf:.2f})", color=(0, 0, 255))
            detected = True 

    if detected:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"detection_{timestamp}.jpg"
        filepath = os.path.join("media", "detections", filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        cv2.imwrite(filepath, annotator.result())

        # Draw labels on full frame using YOLO annotator
        crew = find_nearest_crew(lat, lon)
        task = CleaningTask.objects.create(
            location=location_link,
            snapshot=f"detections/{filename}",
            description="Detected via CCTV",
            assigned_to=crew,
            status="assigned" if crew else "pending"
        )

        print(f"✅ Detected at {timestamp}, task created. Assigned to: {crew.full_name if crew else 'None'}")

        # Send appropriate email with labeled image
        if crew:
            send_detection_alert_email(filepath, location_link, timestamp, crew)
        else:
            send_admin_alert_email(filepath, location_link, timestamp)

        last_alert_time = time.time()

    cv2.imshow("Smart Waste Detection", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
