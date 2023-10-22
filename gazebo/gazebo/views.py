from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from .models import Course, SystemState
from .forms import RegisterForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.http import HttpResponseRedirect
import datetime

def list_courses(request):
    state = status_finder()
    if state == "closed":
        return render(request, 'courses/closed.html')
    else:
        courses = Course.objects.all()
        return render(request, 'courses/list_courses.html', {'courses': courses})

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Log the user in.
            login(request, user)
            return redirect('list_courses')
    else:
        form = RegisterForm()
    return render(request, 'registration/registration.html', {'form': form})

# need view function to redirect to course listing (/courses) or dashboard view instead of /accounts/profile
def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                if user.is_superuser:
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
    semester = sem()
    state = status_finder()
    entry = SystemState.objects.all().filter(semester=semester)[0]
    if(request.GET.get('mybtn')):
        toggle(entry)
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    message = make_message(semester, state)
    return render(request, 'admin/status_change.html', {'message': message})

def make_message(semester, state):
    message = ''
    if state == "open":
        message = semester + " watch period is open"
    elif state == "closed":
        message = semester + " watch period is closed"
    else:
        message = "Error"
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