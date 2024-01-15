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
    Course = apps.get_model("gazebo", "Course")

    watches = Watch.objects.all()

    for watch in watches:
        number = watch.section.course_number
        course_name = Course.objects.get(number=number).name
        response1 = course_by_code(number)
        dfResponse1 = json.loads(response1.content)
        if response1 != [] and dfResponse1[0]:
            response2 = waitlist_activity_api(dfResponse1[0]['courseOffering']['id'])
            dfResponse2 = json.loads(response2.content)
            if response2.status_code != 200 or dfResponse2 == []:
                continue
            current_enrollment = -1
            for section_index in dfResponse2:
                if watch.section.section_number == section_index['activityOffering']['activityCode']:
                    if section_index['activitySeatCount'] == []:
                        continue
                    else:
                        current_enrollment = section_index['activitySeatCount']['used']
            # Email capabilities
            student_email = watch.student.email         
            open_seats = watch.section.capacity - current_enrollment
            if open_seats > watch.num_students and current_enrollment >= 0:
                message = f"""
                    {number} {course_name} has open seats! There are at least {watch.num_students} spot(s) available.
                    
                    Register now: https://eaen.bc.edu/student-registration/#/
                """
                subject = f"{course_name} has open seats!"
                send_mail(subject=subject, message=message, from_email=settings.EMAIL_HOST_USER, recipient_list=[student_email], fail_silently=True)


def start_scheduler():
    if not scheduler.running:
        scheduler.add_job(check_course_availability, "interval", hours=6)
        scheduler.start()

start_scheduler()