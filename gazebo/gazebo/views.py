from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from .models import Course, SystemState
from .forms import RegisterForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
import datetime

def list_courses(request):
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
    month = datetime.datetime.now().month
    semester = ''
    year = datetime.datetime.now().year
    if month >= 10 or month < 3:
        semester = "Spring " + str(year)
    else:
        semester = "Fall " + str(year)
    
    entry = SystemState.objects.all().filter(semester=semester)
    state = ''
    if entry:
        state = entry[0].state 
    else:
        state = "closed"
        new_entry = SystemState(semester = semester, state = "closed")
        new_entry.save()
    
    message = ''
    if state == "open":
        message = semester + " watch period is open"
    elif state == "closed":
        message = semester + " watch period is closed"
    else:
        message = "Error"
    return render(request, 'admin/status_change.html', {'message': message})