# Code_Mystics
# 🧠 AI Waste Management System 

This project is a smart waste management web application designed to help municipal administrators monitor and manage garbage and spill detection tasks using AI-powered CCTV cameras. The system automates the process of detection, reporting, crew assignment, and real-time monitoring.

## 🚀 Features

- ✅ **Admin Dashboard**: Clean UI with sections for profile, crew management, detection status, system logs, and complaints.
- 📸 **AI Detection**: Live monitoring of spills and garbage using YOLO-based object detection models.
- 👷 **Crew Management**:
  - View all cleaning crew members.
  - Assign area and salary for unverified members.
  - Verify crew members directly via the dashboard.
- 📍 **Location-Based Assignment**: Detection events are assigned to the nearest available crew.
- 📨 **Email Alerts**: Admin is notified via email upon new detections and assignments.
- 📊 **System Logs**: Track detection history and crew performance.
- 💬 **Complain Box**: Handle user and crew feedback efficiently.

## 🛠️ Tech Stack

- **Backend**: Django (Python)
- **Frontend**: HTML, CSS, JavaScript (Vanilla)
- **AI Model**: YOLOv8 (Trained for garbage and spill detection)
- **Database**: SQLite (default, can be upgraded to PostgreSQL)
- **Deployment**: Localhost / can be deployed to any WSGI-compatible server


