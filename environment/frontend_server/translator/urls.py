from django.urls import path, re_path

from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("robots.txt", views.robots, name="robots"),

    path("pen_test/trash/", views.trash, name="trash"),
    path("pen_test/info/", views.pen_info, name="pen_info"),
    path("pen_test/info/update/", views.pen_info_update, name="pen_info_update"),
    path("pen_test/compress/", views.compress_pen_test, name="compress_pen_test"),
    path("pen_test/delete/", views.delete_pen_test, name="delete_pen_test"),

    re_path(r"^pen_test/(?:(?P<pen_code>[\w-]+)/)?(?:(?P<step>\d+)/)?(?:(?P<speed>\d+)/)?$", views.pen_test, name="pen_test"),
    re_path(r"^pen_test/(?P<pen_code>[\w-]+)/state/$", views.persona_state, name="persona_state"),
]

websocket_urlpatterns = [
    path("ws/reverie/", views.ReverieConsumer.as_asgi())
]
