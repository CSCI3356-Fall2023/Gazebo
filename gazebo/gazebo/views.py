from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login, authenticate, get_user_model
import pandas as pd
from gazebo.models import Course, SystemState
from django.contrib.auth.forms import AuthenticationForm
from gazebo.models import CustomUser
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.http import JsonResponse
import datetime
from .forms import StudentSignUpForm, AdminSignUpForm
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.db.models import Q

# OAuth2 Imports
import json
from authlib.integrations.django_client import OAuth
from django.conf import settings
from django.urls import reverse
from urllib.parse import quote_plus, urlencode

import requests


oauth = OAuth()

oauth.register(
    "auth0",
    client_id=settings.AUTH0_CLIENT_ID,
    client_secret=settings.AUTH0_CLIENT_SECRET,
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f"https://{settings.AUTH0_DOMAIN}/.well-known/openid-configuration",
)

def login(request):
    return oauth.auth0.authorize_redirect(
        request, request.build_absolute_uri(reverse("callback"))
    )

def callback(request):
    token = oauth.auth0.authorize_access_token(request)
    userinfo = token.get('userinfo')

    email = userinfo.get("email")
    name = userinfo.get("name")

    if not is_valid_email(email):
        messages.error(request, "You must use a BC email to sign in!")
        return redirect(reverse('landing'))

    User = get_user_model()
    user, created = User.objects.get_or_create(
        email=email, 
        defaults={
            "username": email, 
            "first_name": get_first_name(name),
            "last_name": get_last_name(name)
        }
    )

    if created:
        auth_login(request, user)   
        request.session['email'] = email
        return redirect('additional_info')

    auth_login(request, user)
    if request.user.is_superuser:
        return redirect('status_change')
    else: 
        return redirect('list_courses')

def is_valid_email(email):
    return email.endswith("@bc.edu")

def get_first_name(name):
    return name.split()[0] if name else ""

def get_last_name(name):
    return name.split()[-1] if name and len(name.split()) > 1 else ""

def additional_info(request):
    email_from_auth0 = request.session.get('email')
    if request.method == 'POST':
        form = StudentSignUpForm(request.POST)
        if form.is_valid():
            try:
                user = CustomUser.objects.get(email=email_from_auth0) 
            except ObjectDoesNotExist:
                messages.error(request, "User not found.")
                return render(request, 'registration/registration.html', {'form': form})

            user.eagle_id = form.cleaned_data.get('eagle_id')
            user.school = form.cleaned_data.get('school')
            user.major = form.cleaned_data.get('major')
            user.minor = form.cleaned_data.get('minor')
            user.save() 

            if user.is_superuser:
                return redirect('status_change')
            else: 
                return redirect('list_courses')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = StudentSignUpForm() 

    return render(request, 'registration/registration.html', {'form': form})

def logout(request):
    request.session.clear()

    return redirect(
        f"https://{settings.AUTH0_DOMAIN}/v2/logout?"
        + urlencode(
            {
                "returnTo": request.build_absolute_uri(reverse("landing")),
                "client_id": settings.AUTH0_CLIENT_ID,
            },
            quote_via=quote_plus,
        ),
    )

def index(request):
    return render(
        request,
        "index.html",
        context={
            "session": request.session.get("user"),
            "pretty": json.dumps(request.session.get("user"), indent=4),
        },
    )

@login_required
def list_courses(request):
    email = request.user.email
    state = status_finder()
    if state == "closed":
        return render(request, 'courses/closed.html')
    else:
        course_filler(request)
        course_code = request.GET.get('course_code')

        # allowing for filtering by multiple different fields
        query = Q()
        if course_code:
            query &= Q(number__icontains=course_code)
        courses = Course.objects.filter(query)

        sort_by = request.GET.get('sort_by')
        if sort_by and sort_by in [field.name for field in Course._meta.get_fields()]:
            courses = courses.order_by(sort_by)       

        return render(request, 'courses/list_courses.html', {
            'courses': courses, 
            'email': email, 
            'course_code': course_code, 
            'sort_by': sort_by
        })

def student_register(request):
    return "foo"
    # form = StudentSignUpForm(request.POST)
    # if form.is_valid():
    #     email = form.cleaned_data.get('email')
    #     is_valid_bc_user = validate_bc_user(email)
    #     if not is_valid_bc_user:

    # else:
    #     print(form.errors)
    #     # validate BC email

    #     # check to see if already in database (don't want duplicates)

    #     # if not, that means first time user --> prompt Google login

    #     # redirect to get additional info (major, minor, etc)
    #     form = StudentSignUpForm(request.POST)
    #     if form.is_valid():
    #         user = form.save()
    #         login(request, user)
    #         return redirect('list_courses')
    #     form = StudentSignUpForm(initial={'school':'CSOM'})
    # return render(request, 'registration/registration.html', {'form': form})

# admin register is now going to be only done through superuser
def admin_register(request):
    if request.method == 'POST':
        form = AdminSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('status_change')
    else:
        form = AdminSignUpForm()
    return render(request, 'registration/registration.html', {'form': form})



def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                if request.user.is_superuser:
                    return redirect('status_change')
                else: 
                    return redirect('list_courses')
        else:
            messages.error(request,"Invalid username or password.")
    form = AuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})


def landing(request):
    return render(request, 'registration/login_and_register.html')

def status_change(request):
    email = request.user.email
    semester = sem()
    state = status_finder()
    entry = SystemState.objects.all().filter(semester=semester)[0]
    if(request.GET.get('mybtn')):
        toggle(entry)
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    message = make_message(semester, state)
    return render(request, 'admin/status_change.html', {'message': message, 'email': email})

def make_message(semester, state):
    message = semester + " watch period is " + f"{state}"
    return message

def status_finder():
    semester = sem()
    entry = SystemState.objects.all().filter(semester=semester)
    state = ''
    if entry:
        state = entry[0].state 
    else:
        state = "closed"
        new_entry = SystemState(semester = semester, state = state)
        new_entry.save()
    return state

def sem():
    month = datetime.datetime.now().month
    semester = ''
    year = datetime.datetime.now().year
    if month >= 10:
        semester = "Spring " + str(year + 1)
    elif month < 3:
        semester = "Spring " + str(year)
    else:
        semester = "Fall " + str(year)
    return semester

def toggle(entry):
    new_state = ""
    if entry.state == "closed":
        new_state = "open"
    else:
        new_state = "closed"
    entry.state = new_state
    entry.save()
    return new_state

#two api functions: one for 
def course_offering_api(request): 
    code = 'ENGL2170' #turn into searchable parameter later
    """ if code is None:
        response = requests.get("http://localhost:8080/waitlist/waitlistcourseofferings?termId=kuali.atp.FA2023-2024&code=ENGL2170")
    else:
        response = requests.get(f"http://localhost:8080/waitlist/waitlistcourseofferings?termId=kuali.atp.FA2023-2024&code={code}")
 """
    response = requests.get("http://localhost:8080/waitlist/waitlistcourseofferings?termId=kuali.atp.FA2023-2024&code=#")
    if response.status_code == 200:
        data = response.json()
        return JsonResponse(data, safe=False)
    else:
        return JsonResponse({'error': 'Failed to fetch data from the API'}, status=500)
    
def waitlist_activity_api(request, id):
    #code = '952e91af-ffb8-471e-b135-04d6d0b02c62' #turn into searchable parameter later
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
    
# daysConverter = {"M": "Monday", "T": "Tuesday", "W": "Wednesday", "Th": "Thursday", "F": "Friday", "S": "Saturday", "Su": "Sunday"}
def course_filler(request):
    response = course_offering_api(request)
    dfResponse = json.loads(response.content)
    for courseIndex in dfResponse:
        number = courseIndex['courseOffering']['courseOfferingCode']

        # prevent dupicates 
        if Course.objects.filter(number=number).exists():
            continue 

        response2 = waitlist_activity_api(request, courseIndex['courseOffering']['id'])
        dfResponse2 = json.loads(response2.content)
        if response2.status_code != 200 or dfResponse2 == []:
            continue
        name = courseIndex['courseOffering']['name'].split(' -- ')[-1]
        description = courseIndex['courseOffering']['descr']['formatted']
        schedules = dfResponse2[0]['scheduleNames'][0].split()
        formatArray = dfResponse2[0]['activityOffering']['formatOfferingName'].split()
        course_type = formatArray[1]
        section = dfResponse2[0]['activityOffering']['activityCode']
        instructor = ''
        if dfResponse2[0]['activityOffering']['instructors'] == []:
            instructor = "None"
        else:
            instructor = dfResponse2[0]['activityOffering']['instructors'][0]['personName']
        days = schedules[len(schedules) - 2]
        time_range_str = schedules[len(schedules) - 1]  
        #time = time_range_str.split("-")
        #start_time = time[0][0:len(time[0]) - 2]  
        #end_time = time[1][0:len(time[1]) - 2]
        locationPieces = schedules[0:len(schedules) - 2]
        location = " ".join(locationPieces)
        capacity = dfResponse2[0]['activityOffering']['maximumEnrollment']
        #current_enrollment = dfResponse2[0]['activitySeatCount']['used']
        new_course = Course(
            number = number,
            name = name,
            course_type = course_type,
            description = description,
            section = section,
            instructor = instructor,
            days = days,
            #start_time = start_time,
            start_time = '14:30:59',
            end_time = '14:30:59',
            #end_time = end_time,
            location = location,
            capacity = capacity,
            #current_enrollment = current_enrollment
            current_enrollment = 20
        )

        new_course.save()


