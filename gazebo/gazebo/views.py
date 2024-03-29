from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login as auth_login, authenticate, get_user_model
from django.contrib.auth.forms import AuthenticationForm
from gazebo.models import CustomUser, Course, Section, Watch, SystemState, History
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.http import JsonResponse
import datetime
from .forms import StudentSignUpForm, AdminSignUpForm
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponse
from django.template.loader import render_to_string

# OAuth2 Imports
import json
from authlib.integrations.django_client import OAuth
from django.conf import settings
from django.urls import reverse
from urllib.parse import quote_plus, urlencode

import requests

import plotly.express as px
import plotly.io as pio
pio.renderers.default = "notebook_connected"

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

def parse_days(selected_days):
    parsed_days = ""
    for day in selected_days:
        parsed_days += day
    return parsed_days

@login_required
def list_courses(request):
    if status_finder() == "closed":
        return render(request, 'courses/closed.html')

    # initialize query for courses and sections
    course_query = Q()
    section_query = Q()

    # course code filter
    course_code = request.GET.get('course_code', '')
    if course_code:
        course_query &= Q(number__icontains=course_code)

    # department filter
    department = request.GET.get('department')
    if department:
        course_query &= Q(number__icontains=department)

    # professor filter
    professor = request.GET.get('professor')
    if professor:
        section_query &= Q(instructor__icontains=professor)

    # days filter
    selected_days = request.GET.getlist('days[]')
    if selected_days:
        selected_days = parse_days(selected_days)  
        section_query &= Q(days__in=selected_days)

    # apply course filter and annotations
    # courses = Course.objects.filter(course_query).annotate(number_of_watches=Count('watch'))
    courses = Course.objects.filter(course_query)

    if len(section_query) > 0:
        # apply section filter and get distinct course IDs
        sections = Section.objects.filter(section_query, course_number__in=courses.values_list('number', flat=True))
        course_ids = Section.objects.filter(section_query, course_number__in=courses.values_list('number', flat=True)).values_list('course_id', flat=True).distinct()

        courses = courses.filter(id__in=course_ids)
    else:
        sections = Section.objects.all()

        # sorting logic
    sort_by = request.GET.get('sort_by', 'number')
    if sort_by == 'number_of_watches':
        courses = courses.order_by('-num_watches')
    else:
        courses = courses.order_by(sort_by)

    if not courses.exists():
        course_filler()
        list_courses(request)

    paginator = Paginator(courses, 10) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    email = request.user.email
    user = request.user

    watched_course_ids = list(Watch.objects.filter(student=user).values_list('section', flat=True))
    watched_course_ids = [int(id) for id in watched_course_ids] 

    is_admin = request.user.is_superuser
    watches = Watch.objects.all()
    return render(request, 'courses/list_courses.html', {
        'page_obj': page_obj,
        'email': email,
        'course_code': course_code,
        'sort_by': sort_by,
        'watched_course_ids': watched_course_ids,
        'is_admin': is_admin,
        'sections': sections,
        'watches': watches,
        'selected_days': selected_days,
    })

@login_required
@require_POST
def toggle_watchlist(request, section_number, course_number):
    section = get_object_or_404(Section, section_number=section_number, course_number=course_number)
    user = request.user

    num_students = int(request.POST.get('num_students'))

    watch_entry, created = Watch.objects.get_or_create(student=user, section=section, num_students=num_students)

    course = get_object_or_404(Course, number=course_number)
    # if we create a watch entry before, toggle it by removing from Watch table
    if not created:
        watch_entry.delete()
    # if not, entry was created and added to watch list so do nothing
    else:
        watches = course.num_watches
        watches += 1
        course.num_watches = watches
        course.save()
        pass

    # handles redirect to the correct page (courselist or watchlist)
    origin = request.POST.get('origin')
    if origin == 'watchlist':
        return redirect('watchlist_view')
    
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

def fill_history():
    watches = Watch.objects.all()
    for watch in watches:
        semester = sem()
        first_name = watch.student.first_name
        last_name = watch.student.last_name
        course_name = watch.section.course_number
        instructor = watch.section.instructor
        if(not History.objects.all().filter(semester=semester, first_name=first_name, last_name=last_name, course_name=course_name, instructor=instructor).exists()):
            new_history = History(
                semester = semester,
                first_name = first_name,
                last_name = last_name,
                course_name = course_name,
                instructor = instructor
            )
            new_history.save()
        else:
            continue

@user_passes_test(lambda u: u.is_superuser)
def admin_report(request, semester=sem(), cont=True):
    email = request.user.email

    filter_metric = request.GET.get('filter_metric', '')
    filter_value = request.GET.get('filter_value', '') 

    fill_history()

    # top level stats

    num_students_with_watches = History.objects.filter(semester=semester).values('first_name', 'last_name').distinct().count()
    watches = History.objects.filter(semester=semester)
    num_watches = len(watches)
    course_counts = watches.values('course_name').annotate(entry_count=Count('course_name'))
    most_watched_course = course_counts.order_by('-entry_count').first()
    max_watches = 0
    if most_watched_course:
        max_watches = watches.filter(course_name = most_watched_course['course_name']).count()
    courses = []
    if filter_metric == 'department':
        courses = watches.filter(number__icontains=filter_value)
    elif filter_metric == 'instructor':
        courses = watches.filter(instructor__icontains=filter_value)
    elif filter_metric == 'course':
        courses = watches.filter(course_name__icontains=filter_value)

    if filter_metric:
        watches = courses

    major_graph = admin_report_major()
    top_courses_graph = admin_report_top_course()
    return render(request, 'admin/admin_report.html', {
        'email': email,
        'num_students_with_watches' : num_students_with_watches,
        'num_watches': num_watches,
        'most_watched_course': most_watched_course,
        "watches": watches,
        'semester': semester,
        'max_watches': max_watches,
        'major_graph': major_graph,
        'top_courses_graph': top_courses_graph,


    })

def landing(request):
    return render(request, 'registration/login_and_register.html')

def status_change(request):
    if (not request.user.is_superuser):
        return redirect('temp_view')
    
    email = request.user.email
    semester = sem()
    states = SystemState.objects.all()

    if (request.GET.get('sem')):
        semester = request.GET.get('sem', '')
        entry = SystemState.objects.all().filter(semester=semester)[0]
        toggle(entry)
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    return render(request, 'admin/status_change.html', {'email': email, 'states': states})

def download_report(request):
    semester = request.GET.get('sem', 'default_semester_value')
    context = {'semester': semester}

    rendered_html = render_to_string('admin/admin_report.html', context, request=request)

    response = HttpResponse(rendered_html, content_type='application/octet-stream')

    response['Content-Disposition'] = 'attachment; filename="admin_report.html"'
    return response

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

def toggle(entry):
    new_state = ""
    if entry.state == "closed":
        new_state = "open"
    else:
        new_state = "closed"
        fill_history()
        Watch.objects.all().delete()
        Course.objects.all().delete()
        Section.objects.all().delete()
    entry.state = new_state
    entry.save()
    return new_state

    
#two api functions: one for calling course list, one for calling section list
def course_offering_api(): 
    response = requests.get("http://localhost:8080/waitlist/waitlistcourseofferings?termId=kuali.atp.FA2023-2024&code=#")
    if response.status_code == 200:
        data = response.json()
        return JsonResponse(data, safe=False)
    
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
    
    return JsonResponse({'error': 'Failed to fetch data from the API'}, status=500)
    

def period_determiner(start_time):
    start_time_pieces = start_time.split(":")
    if "AM" in start_time:
        return "Morning"
    
    if "PM" in start_time:
        if int(start_time_pieces[0]) in range(1,5) or start_time_pieces[0] == "12":
            return "Afternoon"
        
        return "Evening"
    
    return "Error!"
        

def course_filler():
    response = course_offering_api()
    dfResponse = json.loads(response.content)
    for courseIndex in dfResponse:
        number = courseIndex['courseOffering']['courseOfferingCode']

        course, created = Course.objects.get_or_create(
            number=number,
            defaults={
                'name': courseIndex['courseOffering']['name'].split(' -- ')[-1],
                'course_level': number[4] + "000",
                'description': courseIndex['courseOffering']['descr']['formatted']
            }
        )

        response2 = waitlist_activity_api(courseIndex['courseOffering']['id'])
        dfResponse2 = json.loads(response2.content)
        if response2.status_code != 200 or dfResponse2 == []:
            continue
        for section_index in dfResponse2:
            course_number = number
            formatArray = section_index['activityOffering']['typeKey'].split(".")
            course_type = formatArray[len(formatArray) - 1]
            section_number = section_index['activityOffering']['activityCode']
            section_id = section_index['activityOffering']['id']
            # prevent duplicates 
            if Section.objects.filter(course_number=number, section_id = section_id).exists():
                continue
            instructor = ''
            if section_index['activityOffering']['instructors'] == []:
                instructor = "None"

            else:
                instructor = section_index['activityOffering']['instructors'][0]['personName']

            capacity = section_index['activityOffering']['maximumEnrollment']
            current_enrollment = ''
            if section_index['activitySeatCount'] == [] or section_index['activitySeatCount'] == None:
                current_enrollment = 20

            else:
                current_enrollment = section_index['activitySeatCount']['used']

            schedules = section_index['scheduleNames']
            for index in range(0, len(schedules)):
                if " Noon" in schedules[index]: 
                    new_entry = schedules[index].replace(" Noon", "PM")
                    schedules[index] = new_entry

            start_time = ""
            end_time = ""
            days = ""
            location = ""
            period_of_day = ""
            if "By Arrangement" in schedules or "BY ARRANGEMENT" in schedules or "By arrangement" in schedules:
                start_time = "By Arrangement"
                end_time = "By Arrangement"
                days = "By Arrangement"
                location = "By Arrangement"
                period_of_day = "By Arrangement"

            elif "On-line Asynchronous" in schedules:
                start_time = "Online Asynchronous"
                end_time = "Online Asynchronous"
                days = "Online Asynchronous"
                location = "Online Asynchronous"
                period_of_day = "Online Asynchronous"

            elif "ONLINE COURSE" in schedules:
                start_time = "Online Course"
                end_time = "Online Course"
                days = "Online Course"
                location = "Online Course"
                period_of_day = "Online Course"

            else:
                disgusting_format = False
                for index in range(0, len(schedules)):
                    if ("Online Asynchronous" in schedules[index] or "<br/>" in schedules[index] 
                        or "Library" in schedules[index] or len(schedules) == 3 or "/" in schedules[index] 
                        or "from" in schedules[index] or "Sunday" in schedules[index] 
                        or "Auditorium" in schedules[index] or "Sept" in schedules[index]
                        or "Advising Section" in schedules[index]):
                        disgusting_format = True

                if disgusting_format == 1:
                    continue

                location_and_time_pieces = []

                if len(schedules) > 1:
                    if "HYBRID course." in schedules or "HYBRID COURSE" in schedules:
                        continue
                    elif "PEP Only" in schedules:
                        continue
                    elif "Meets weekly" in schedules[0] or "Meets weekly" in schedules[1] or "Open to Law School" in schedules[0] or "Open to Law School" in schedules[1]:
                        continue
                    elif "room TBA" in schedules[0] or "room TBA" in schedules[1]:
                        location = "TBA"
                    elif "Hybrid." in schedules[0] or "Hybrid." in schedules[1]:
                        continue
                    elif "Hybrid Course" in schedules:
                        continue
                    elif "McMullen Museum" in schedules:
                        location = "McMullen Museum"
                        days = schedules[0]
                        times = schedules[1]
                        continue
                    elif len(schedules[0]) == len(schedules[1]):
                        continue
                    elif schedules[1] == "International Human Rights Practicum":
                        continue
                    elif "This lab section is not offered in Fall 2023." in schedules:
                        continue
                    else:
                        sub1 = ""
                        sub2 = []
                        location_and_time_pieces.append(schedules[0])
                        location_and_time_pieces.append(schedules[1])
                        if "Hall" in location_and_time_pieces[0] and "Hall" in location_and_time_pieces[1]:
                            sub1 = location_and_time_pieces[1]
                            sub2 = sub1.split()
                            location = " ".join(sub2[0:len(sub2) - 3])
                            days = sub2[len(sub2) - 3]
                            times = sub2[len(sub2) - 1].split("-")
                            start_time = times[0]
                            end_time = times[1]
                            period_of_day = period_determiner(start_time)
                            continue

                        if "AM" in location_and_time_pieces[0] or "PM" in location_and_time_pieces[0]:
                            location = location_and_time_pieces[1]
                            days_and_times = location_and_time_pieces[0].split()
                            days = days_and_times[0]
                            times = days_and_times[1].split("-")
                            start_time = times[0]
                            if (len(times) > 1 and times[1]):
                                end_time = times[1]
                            period_of_day = period_determiner(start_time)

                        if "AM" in location_and_time_pieces[1] or "PM" in location_and_time_pieces[1]:
                            location = location_and_time_pieces[0]
                            days_and_times = location_and_time_pieces[1].split()
                            days = days_and_times[0]
                            times = days_and_times[1].split("-")
                            start_time = times[0]
                            if (len(times) > 1 and times[1]):
                                end_time = times[1]
                            period_of_day = period_determiner(start_time)

                else:
                    location_and_time_pieces = schedules[0].split()
                    if len(location_and_time_pieces) == 2:
                        if "Hall" in location_and_time_pieces:
                            location = location_and_time_pieces[0]
                            days_and_times = location_and_time_pieces[1].split()
                            days = days_and_times[0]
                            times = days_and_times[1].split("-")
                            start_time = times[0]
                            end_time = times[1]
                            period_of_day = period_determiner(start_time)

                        else:
                            days = location_and_time_pieces[0]
                            times = location_and_time_pieces[1].split("-")
                            start_time = times[0]
                            end_time = times[1]
                            period_of_day = period_determiner(start_time)

                    else:
                        locationPieces = location_and_time_pieces[0:len(location_and_time_pieces) - 2]
                        location = " ".join(locationPieces)
                        days = location_and_time_pieces[len(location_and_time_pieces) - 2]
                        times = location_and_time_pieces[len(location_and_time_pieces) - 1].split("-")
                        start_time = times[0]
                        end_time = times[1]
                        period_of_day = period_determiner(start_time)

            if not Section.objects.filter(course_number=number, section_id=section_id).exists():
                new_section = Section(
                    course=course,  
                    course_number=course_number,
                    section_number=section_number,
                    section_id=section_id,
                    course_type=course_type,
                    instructor=instructor,
                    days=days,
                    location=location,
                    start_time=start_time, 
                    end_time=end_time,
                    period_of_day=period_of_day,
                    capacity=capacity,
                    current_enrollment=current_enrollment
                )
                new_section.save()

        # prevent duplicates 
        # if Course.objects.filter(number=number).exists():
        #     continue

        # new_course = Course(
        #     number = number,
        #     name = name,
        #     course_level = course_level,
        #     description = description
        # )
        # new_course.save()

def watchlist_view(request):
    user = request.user
    watches = Watch.objects.filter(student=user)
    sections = Section.objects.filter(watch__in=watches)
    return render(request, 'watchlist.html', {'watches': watches })

def temp_view(request):
    return render(request, 'error.html')

def admin_report_major():
    majors = Watch.objects.values('student__major').annotate(count=Count('student__major')).exclude(student__major='')
    major_names = [item['student__major'] for item in majors]
    major_counts = [item['count'] for item in majors]
    # Creating the Plotly figure
    fig = px.pie(names=major_names, values=major_counts, title= 'Majors of Students Watching', hole= .5,  color_discrete_sequence=px.colors.sequential.RdBu)
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    major_graph = fig.to_html(full_html=False, config={'displayModeBar': False})
    # Rendering the template with the graph
    return major_graph

def admin_report_top_course():
    query_results = Course.objects.order_by('-num_watches')[:10]
    course_names = [item.number for item in query_results]
    watch_counts = [item.num_watches for item in query_results]

    fig = px.bar(x=course_names, y=watch_counts, title='Top 10 Most Watched Courses', color_discrete_sequence=px.colors.sequential.RdBu)
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis_title="", 
        yaxis_title ="count"
       
    )
    return fig.to_html(full_html=False, config={'displayModeBar': False})
