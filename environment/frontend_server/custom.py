from django.shortcuts import redirect
from django.conf import settings
from django.urls import reverse, resolve

from utils import black_hats, white_hats



def processors(request):
    return {
        "site": {
            "lang": settings.LANGUAGE_CODE.split("-")[0],
            "title": "Persona",
            "hide": settings.LOGIN_REQUIRED is True and not request.user.is_authenticated,
            "mode": settings.THEME.lower(),
        },
        "nav": [
            {
                "icon": "fa-solid fa-gauge",
                "name": "Dashboard",
                "href": reverse("dashboard"),
            }, {
                "icon": "fa-solid fa-play",
                "name": "Penetration Test",
                "href": reverse("pen_test"),
            },
        ],
        "black_hats": black_hats,
        "white_hats": white_hats,
    }



class LoginCheck:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if settings.LOGIN_REQUIRED is True and not request.user.is_authenticated:
            try:
                url_name = resolve(request.path_info).url_name
            except:
                url_name = None
            if not url_name or (url_name != settings.LOGIN_URL and request.path_info != settings.LOGIN_URL):
                return redirect(settings.LOGIN_URL)
        return self.get_response(request)
