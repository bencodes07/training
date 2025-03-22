from typing import Optional

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, HttpResponseRedirect, reverse, redirect

from lists.models import Course
from logs.models import Log
from .forms import CommentForm

from connect.views import mentor_groups


def split_active_inactive(logs, courses, trainee):
    active = {}
    inactive = {}
    active_courses = set(trainee.active_courses.all())

    non_active = courses - active_courses
    for course in active_courses:
        active[course] = logs.filter(course=course).order_by("-session_date")

    for course in non_active:
        inactive[course] = logs.filter(course=course).order_by("-session_date")

    return active, inactive


@login_required
def home(request):
    logs = Log.objects.filter(trainee=request.user)
    # Get all courses from the logs
    courses = set(Course.objects.filter(log__in=logs))

    active, inactive = split_active_inactive(logs, courses, request.user)

    return render(
        request, "trainee/home.html", {"active": active, "inactive": inactive}
    )


@login_required
def mentor_view(request, vatsim_id: int):
    trainee = get_object_or_404(User, username=vatsim_id)
    courses = request.user.mentored_courses.all()
    if request.user.is_superuser:
        courses = Course.objects.all()

    if not request.user.groups.filter(name__in=mentor_groups).exists():
        return redirect("/")
    # Get all logs for the trainee that are in the courses
    logs = Log.objects.filter(trainee=trainee, course__in=courses).order_by(
        "-session_date"
    )
    # Get all courses from the logs
    courses = set(Course.objects.filter(log__in=logs))
    active, inactive = split_active_inactive(logs, courses, trainee)

    comments = trainee.comments.all().order_by("-date_added")
    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            text = form.cleaned_data["text"]
            author = request.user
            trainee.comments.create(text=text, author=author)
            return HttpResponseRedirect(
                reverse("trainee:mentor_view", args=[trainee.username])
            )
    else:
        form = CommentForm()

    return render(
        request,
        "trainee/mentor_view.html",
        {"active": active, "inactive": inactive, "comments": comments, "form": form},
    )
