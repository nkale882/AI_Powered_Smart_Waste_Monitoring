from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import make_password, check_password
import json
from .models import Admin, CleaningCrew, Position, CleaningTask
from rest_framework.decorators import api_view
from rest_framework.response import Response


# Utility function to get or create position
def get_or_create_position(role):
    position, _ = Position.objects.get_or_create(name=role.lower())
    return position

def home(request):
    return render(request, 'index.html')

def admin_home(request):
    
    crew_members = CleaningCrew.objects.all()
    detections = CleaningTask.objects.all()
    return render(request, 'adminHome.html', {
        'crew_members': crew_members,
        'detections': detections
    })

def crews_home(request):
    return render(request, 'crewHome.html')

@csrf_exempt
def signup_admin(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            if Admin.objects.filter(email=data['email']).exists():
                return JsonResponse({'message': 'Admin already exists'}, status=400)

            Admin.objects.create(
                full_name=f"{data['first_name']} {data['last_name']}",
                phone_number=data['phone_number'],
                email=data['email'],
                password=make_password(data['password']),
            )
            return JsonResponse({'message': 'Admin signed up successfully'}, status=201)
        except Exception as e:
            return JsonResponse({'message': str(e)}, status=500)

@csrf_exempt
def signup_crew(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            if CleaningCrew.objects.filter(email=data['email']).exists():
                return JsonResponse({'message': 'Crew already exists'}, status=400)

            CleaningCrew.objects.create(
                full_name=data['full_name'],
                phone_number=data['phone_number'],
                email=data['email'],
                password=make_password(data['password']),
                address=data.get('address', ''),
                verified=False,
                experience_years=data.get('experience_years', 0),
            )
            return JsonResponse({'message': 'Crew signed up successfully'}, status=201)
        except Exception as e:
            return JsonResponse({'message': str(e)}, status=500)

@csrf_exempt
def login_admin(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user = Admin.objects.get(email=data['email'])
            if check_password(data['password'], user.password):
                return JsonResponse({'message': 'Admin login successful', 'user_id': user.id}, status=200)
            return JsonResponse({'message': 'Invalid password'}, status=401)
        except Admin.DoesNotExist:
            return JsonResponse({'message': 'Admin not found'}, status=404)

@csrf_exempt
def login_crew(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user = CleaningCrew.objects.get(email=data['email'])
            
            # Check if the crew is verified
            if not user.verified:
                return JsonResponse({'message': 'Account not verified. Please wait for admin approval.'}, status=403)

            if check_password(data['password'], user.password):
                return JsonResponse({'message': 'Crew login successful', 'user_id': user.id}, status=200)
            
            return JsonResponse({'message': 'Invalid password'}, status=401)
        
        except CleaningCrew.DoesNotExist:
            return JsonResponse({'message': 'Crew member not found'}, status=404)

from django.core.mail import EmailMultiAlternatives
from django.conf import settings

def send_verification_email(crew):
    subject = "Crew Verification Successful"
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = [crew.email]

    text_content = f"Hello {crew.full_name}, your verification is complete."

    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f2f2f2; padding: 20px;">
      <div style="background-color: #fff; padding: 20px; border-radius: 8px; max-width: 600px; margin: auto; border: 1px solid #ccc;">
        <h2 style="color: #28a745;">Verification Successful ✅</h2>
        <p style="font-size: 16px; color: #333;">Hello <strong>{crew.full_name}</strong>,</p>
        <p style="font-size: 16px; color: #333;">Your crew profile has been <strong>successfully verified. Now you can access smart facilities. </strong>.</p>
        <p style="font-size: 16px; color: #333;"><strong>Assigned Area:</strong> {crew.assigned_area}</p>
        <p style="font-size: 16px; color: #333;"><strong>Annual Salary:</strong> ₹{crew.annual_salary}</p>
        <br>
        <p style="font-size: 14px; color: #555;">Thank you for being part of our Smart Waste Management System!</p>
        <p style="font-size: 14px; color: #555;">– Admin Team</p>
      </div>
    </body>
    </html>
    """

    msg = EmailMultiAlternatives(subject, text_content, from_email, to_email)
    msg.attach_alternative(html_content, "text/html")
    msg.send()


@csrf_exempt
def view_crews(request):
    crew_members = CleaningCrew.objects.all()

    if request.method == 'POST':
        crew_id = request.POST.get('crew_id')
        assigned_area = request.POST.get('assigned_area')
        annual_salary = request.POST.get('annual_salary')

        crew = CleaningCrew.objects.get(id=crew_id)
        crew.verified = True
        crew.assigned_area = assigned_area
        crew.annual_salary = annual_salary
        crew.save()
        try:
            send_verification_email(crew)
        except Exception as e:
            print(f"Failed to send verification email: {e}")

        return JsonResponse({'message': 'Crew Verification successful'},status=200)

    return render(request, 'adminHome.html', {'crew_members': crew_members})

@csrf_exempt
def detection_list_api(request):
    detections = CleaningTask.objects.all().order_by('-created_date')
    data = []

    for task in detections:
        data.append({
            "id": task.id,
            "location": task.location,
            "snapshot": request.build_absolute_uri(task.snapshot.url) if task.snapshot else None,
            "assigned_to": task.assigned_to.full_name if task.assigned_to else "Not Assigned",
            "status": task.status,
            "created_date": task.created_date.strftime("%Y-%m-%d %H:%M:%S"),
        })

    return Response(data)