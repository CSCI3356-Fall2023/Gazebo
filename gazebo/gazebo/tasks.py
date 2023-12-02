from .models import Watch
from .views import *

def check_course_availability():

    watches = Watch.objects.all()

    for watch in watches:
        number = watch.course.number
        response1 = course_by_code(number)
        dfResponse1 = json.loads(response1.content)
        if response1 != []:
            response2 = waitlist_activity_api(dfResponse1[0]['courseOffering']['id'])
            dfResponse2 = json.loads(response2.content)
            if response2.status_code != 200 or dfResponse2 == []:
                continue
            current_enrollment = 0
            if dfResponse2[0]['activitySeatCount'] == []:
                continue
            else:
                current_enrollment = dfResponse2[0]['activitySeatCount']['used']
            # Add email capabilities here
            if current_enrollment < watch.course.capacity:
                print(f'{number} is open!')

        
