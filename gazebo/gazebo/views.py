from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login as auth_login, authenticate, get_user_model
import pandas as pd
from gazebo.models import Course, SystemState
from django.contrib.auth.forms import AuthenticationForm
from gazebo.models import CustomUser, Course, Watch
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.http import JsonResponse
import datetime
from .forms import StudentSignUpForm, AdminSignUpForm
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Prefetch, Count
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import user_passes_test

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
    user = request.user
    
    course_code = request.GET.get('course_code', '')
    sort_by = request.GET.get('sort_by', 'number') 

    query = Q()
    if course_code:
        query &= Q(number__icontains=course_code)

    courses = Course.objects.filter(query).annotate(number_of_watches=Count('watch'))

    if sort_by == 'number_of_watches':
        courses = courses.order_by('-number_of_watches')
    else:
        courses = courses.order_by(sort_by)

    paginator = Paginator(courses, 10) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    
    watched_course_ids = list(Watch.objects.filter(student=user).values_list('course', flat=True))
    watched_course_ids = [int(id) for id in watched_course_ids] 

    is_admin = request.user.is_superuser

    return render(request, 'courses/list_courses.html', {
        'page_obj': page_obj,
        'email': email,
        'course_code': course_code,
        'sort_by': sort_by,
        'watched_course_ids': watched_course_ids,
        'is_admin': is_admin,
    })

@login_required
@require_POST
def toggle_watchlist(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    user = request.user

    watch_entry, created = Watch.objects.get_or_create(student=user, course=course)

    # if we create a watch entry before, toggle it by removing from Watch table
    if not created:
        watch_entry.delete()
    # if not, entry was created and added to watch list so do nothing
    else:
        pass

    # handles redirect to the correct page (courselist or watchlist)
    origin = request.POST.get('origin')
    if origin == 'watchlist':
        return redirect('watchlist_view')
    else:
        course_code = request.POST.get('course_code', '')
        sort_by = request.POST.get('sort_by', '')
        return redirect(f'/courses/?course_code={course_code}&sort_by={sort_by}')

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
            messages.error(request, "Invalid username or password.")
    form = AuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})

def admin_login(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password) 
            if user is not None:
                auth_login(request, user)
                if user is not None and request.user.is_superuser:
                    return redirect('status_change')
        messages.error(request, "Invalid login")
    form = AuthenticationForm()
    return render(request, 'admin/login.html', { 'form': form })

def admin_course_list(request):
    return render(request, 'admin/course_list.html')

@user_passes_test(lambda u: u.is_superuser)
def admin_report(request):
    email = request.user.email

    filter_metric = request.GET.get('filter_metric', '')
    filter_value = request.GET.get('filter_value', '') 

    courses = Course.objects.all()

    # top level stats
    num_students_with_watches = Watch.objects.values('student').distinct().count()
    watches = Watch.objects.all()
    num_watches = len(watches)
    most_watched_course = Course.objects.values().annotate(number_of_watches=Count('watch')).order_by('-number_of_watches')[0]

    if filter_metric == 'department':
        courses = courses.filter(number__icontains=filter_value)
    elif filter_metric == 'instructor':
        courses = courses.filter(instructor__icontains=filter_value)
    elif filter_metric == 'course':
        courses = courses.filter(name__icontains=filter_value)

    if filter_metric:
        watches = watches.filter(course__in=courses)

    return render(request, 'admin/admin_report.html', {
        'email': email,
        'num_students_with_watches' : num_students_with_watches,
        'num_watches': num_watches,
        'most_watched_course': most_watched_course,
        "watches": watches
    })

def landing(request):
    return render(request, 'registration/login_and_register.html')

def status_change(request):
    if(not request.user.is_superuser):
        return redirect('temp_view')
    
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

    
#two api functions: one for calling course list, one for calling section list
def course_offering_api(): 
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
    
# daysConverter = {"M": "Monday", "Tu": "Tuesday", "W": "Wednesday", "Th": "Thursday", "F": "Friday", "S": "Saturday", "Su": "Sunday"}
def course_filler():
    response = course_offering_api()
    dfResponse = json.loads(response.content)
    for courseIndex in dfResponse:
        number = courseIndex['courseOffering']['courseOfferingCode']

        # prevent dupicates 
        if Course.objects.filter(number=number).exists():
            continue 

        response2 = waitlist_activity_api(courseIndex['courseOffering']['id'])
        dfResponse2 = json.loads(response2.content)
        if response2.status_code != 200 or dfResponse2 == []:
            continue
        name = courseIndex['courseOffering']['name'].split(' -- ')[-1]
        course_level = name[4] + "000"
        description = courseIndex['courseOffering']['descr']['formatted']
        schedules = dfResponse2[0]['scheduleNames'][0].split()
        formatArray = dfResponse2[0]['activityOffering']['typeKey'].split(".")
        course_type = formatArray[len(formatArray) - 1]
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
        current_enrollment = ''
        if dfResponse2[0]['activitySeatCount'] == []:
            current_enrollment = 20
        else:
            current_enrollment = dfResponse2[0]['activitySeatCount']['used']
        new_course = Course(
            number = number,
            name = name,
            # course_level = course_level,
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
            current_enrollment = current_enrollment
        )

        new_course.save()

# def toggle_watchlist(request, course_id):
#     if request.method == 'POST':
#         user = request.user
#         course = get_object_or_404(Course, id=course_id)
#         watch, created = Watch.objects.get_or_create(student=user, course=course)
#         if not created:
#             watch.delete()
#             added = False
#         else:
#             added = True
#         return JsonResponse({'added': added})
#     return JsonResponse({'status': 'error'}, status=400)

def watchlist_view(request):
    user = request.user
    watches = Watch.objects.filter(student=user)
    courses = Course.objects.filter(watch__in=watches)
    return render(request, 'watchlist.html', {'courses': courses})

def temp_view(request):
    return render(request, 'error.html')


