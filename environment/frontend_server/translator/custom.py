from django.conf import settings
from django.urls import reverse



def processors(request):
    return {
        "site": {
            "lang": settings.LANGUAGE_CODE.split("-")[0],
            "title": "Reverie",
        },
        "nav": [
            {
                "icon": "fa-solid fa-gauge",
                "name": "Dashboard",
                "href": reverse("dashboard"),
            }, {
                "icon": "fa-solid fa-play",
                "name": "Simulations",
                "href": reverse("simulator"),
            },
        ],
    }
