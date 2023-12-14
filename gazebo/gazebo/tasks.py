import json
import requests
from django.http import JsonResponse

from django.core.mail import send_mail
from django.conf import settings
from apscheduler.schedulers.background import BackgroundScheduler
from django.apps import apps

scheduler = BackgroundScheduler()

def course_by_code(code):
    if code is None:
        response = requests.get("http://localhost:8080/waitlist/waitlistcourseofferings?termId=kuali.atp.FA2023-2024&code=ENGL2170")
    else:
        response = requests.get(f"http://localhost:8080/waitlist/waitlistcourseofferings?termId=kuali.atp.FA2023-2024&code={code}")
    if response.status_code == 200:
        data = response.json()
        return JsonResponse(data, safe=False)
    else:
        return JsonResponse({'error': 'Failed to fetch data from the API'}, status=500)

def waitlist_activity_api(id):
    code = id
    if code is None:
        response = requests.get("http://localhost:8080/waitlist/waitlistactivityofferings?courseOfferingId=952e91af-ffb8-471e-b135-04d6d0b02c62")
    else:
        response = requests.get(f"http://localhost:8080/waitlist/waitlistactivityofferings?courseOfferingId={code}") 

    if response.status_code == 200:
        data = response.json()
        return JsonResponse(data, safe=False)
    else:
        return JsonResponse({'error': 'Failed to fetch data from the API'}, status=500)
    
def check_course_availability():

    Watch = apps.get_model("gazebo", "Watch")

    watches = Watch.objects.all()

    for watch in watches:
        number = watch.section.course_number
        response1 = course_by_code(number)
        dfResponse1 = json.loads(response1.content)
        if response1 != [] and dfResponse1[0]:
            response2 = waitlist_activity_api(dfResponse1[0]['courseOffering']['id'])
            dfResponse2 = json.loads(response2.content)
            if response2.status_code != 200 or dfResponse2 == []:
                continue
            current_enrollment = 0
            if dfResponse2[0]['activitySeatCount'] == []:
                continue
            else:
                current_enrollment = dfResponse2[0]['activitySeatCount']['used']
            # Email capabilities
            student_email = watch.student.email            
            if current_enrollment < watch.course.capacity:
                send_mail(f'{number} is open!',  f'{number} is open!', settings.EMAIL_HOST_USER, [student_email], fail_silently=True)
                print(f'{number} is open!')


def start_scheduler():
    if not scheduler.running:
        scheduler.add_job(check_course_availability, "interval", hours=6)
        scheduler.start()

start_scheduler()