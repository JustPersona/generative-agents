from django.urls import path, re_path

from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("robots.txt", views.robots, name="robots"),

    path("pens/trash/", views.trash, name="trash"),
    path("pens/info/", views.pen_info, name="pen_info"),
    path("pens/info/update/", views.pen_info_update, name="pen_info_update"),
    path("pens/compress/", views.compress_pen_test, name="compress_pen_test"),
    path("pens/delete/", views.delete_pen_test, name="delete_pen_test"),

    re_path(r"^pens/(?:(?P<pen_code>[\w-]+)/)?(?:(?P<step>\d+)/)?(?:(?P<speed>\d+)/)?$", views.pen_test, name="pen_test"),
    re_path(r"^pens/(?P<pen_code>[\w-]+)/state/$", views.persona_state, name="persona_state"),
]

websocket_urlpatterns = [
    path("ws/reverie/", views.ReverieConsumer.as_asgi())
]
