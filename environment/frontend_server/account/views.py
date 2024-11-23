import json

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods

from django.contrib.auth import authenticate, login, logout
from django.core.validators  import validate_email
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from django.db import transaction
from django.db.models import Q
from django.forms.models import model_to_dict
from django.contrib.auth.models import User



# Functions

def user_to_dict(user, *, curr_user=None):
    data = model_to_dict(user)
    data["date_joined"] = user.date_joined.strftime("%Y-%m-%d %H:%M:%S")
    if data["last_login"]: data["last_login"] = user.last_login.strftime("%Y-%m-%d %H:%M:%S")
    if "password" in data: del data["password"]
    data["curr_user"] = curr_user == user
    return data



# Views

@require_http_methods(["POST"])
def signout(request):
    logout(request)
    return HttpResponse()

@require_http_methods(["GET", "POST"])
def signin(request):
    if request.user.is_authenticated:
        return redirect(settings.LOGIN_REDIRECT_URL)
    
    if request.method == "GET":
        return render(request, "pages/signin.html", {"num_of_users": User.objects.count() != 0})

    data = json.loads(request.body)
    try:
        username = data["username"].strip()
        password = data["password"].strip()
        if not username or not password: raise
    except KeyError:
        return HttpResponse(status=400)
    except:
        return HttpResponse("Please fill in all the fields", status=400)

    user = authenticate(request, username=username, password=password)
    if user is None:
        return HttpResponse("Authentication failed", status=401)

    login(request, user)
    return HttpResponse()

@require_http_methods(["GET"])
def manage(request):
    if not request.user.is_superuser:
        return HttpResponse(status=404)

    users = [user_to_dict(user, curr_user=request.user) for user in User.objects.all()]
    context = {
        "users": json.dumps(users),
        "total": len(users),
    }
    return render(request, "pages/manage.html", context)

@require_http_methods(["POST"])
def user(request):
    if not request.user.is_superuser:
        return HttpResponse(status=404)

    data = json.loads(request.body)

    try:
        user = User.objects.get(id=data["userid"].strip())
        user = user_to_dict(user, curr_user=request.user)
        return JsonResponse(user)
    except:
        return HttpResponse(status=400)

@require_http_methods(["POST"])
def user_update(request):
    if not request.user.is_superuser:
        return HttpResponse(status=404)

    data = json.loads(request.body)
    update = data.get("update") is not False

    userid = data.get("userid", "").strip()
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    email = data.get("email", "").strip()

    try:
        if update:
            if not userid:
                return HttpResponse(status=400)
            user = User.objects.get(id=userid)
            if username:
                if User.objects.filter(~Q(id=user.id) & Q(username=username)):
                    return JsonResponse({"username": "Already exists"}, status=409)
                user.username = username
            if password:
                validate_password(password)
                user.set_password(password)
        else:
            if not username:
                return JsonResponse({"username": "Required information"}, status=400)
            elif User.objects.filter(username=username):
                return JsonResponse({"username": "Already exists"}, status=409)
            elif not password:
                return JsonResponse({"password": "Required information"}, status=400)
            validate_password(password)
            user = User.objects.create_user(username=username, password=password)
    except ValidationError as e:
        return JsonResponse({"password": e.messages[0]}, status=400)
    except ValueError as e:
        return HttpResponse(status=400)

    if email:
        try:
            validate_email(email)
            user.email = email
        except:
            return JsonResponse({"email": "Invalid format"}, status=400)

    is_staff = data.get("is_staff") is True
    is_active = data.get("is_active") is True

    user.first_name = data.get("first_name", "")
    user.last_name = data.get("last_name", "")
    user.is_active = is_active
    user.is_staff = user.is_superuser or is_staff
    user.save()

    user = user_to_dict(user, curr_user=request.user)
    return JsonResponse(user)

@require_http_methods(["POST"])
def user_delete(request):
    if not request.user.is_superuser:
        return HttpResponse(status=404)

    userid = json.loads(request.body).get("userid")
    try:
        with transaction.atomic():
            user = User.objects.get(id=userid)
            user.delete()
    except:
        return HttpResponse(status=500)
    return JsonResponse({"id": userid})
