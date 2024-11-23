from django.urls import path, re_path

from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("robots.txt", views.robots, name="robots"),
    path("trash/", views.trash, name="trash"),

    re_path(r"^pen_test/(?:(?P<pen_code>[\w-]+)/)?(?:(?P<step>\d+)/)?(?:(?P<speed>\d+)/)?$", views.pen_test, name="pen_test"),
    re_path(r'^replay_persona_state/(?P<pen_code>[\w-]+)/(?P<step>[\w-]+)/(?P<persona_name>[\w-]+)/$', views.replay_persona_state, name='replay_persona_state'),

    path("pen_info/", views.pen_info, name="pen_info"),
    path("pen_info_update/", views.pen_info_update, name="pen_info_update"),
    path("compress_pen_test/", views.compress_pen_test, name="compress_pen_test"),
    path("delete_pen_test/", views.delete_pen_test, name="delete_pen_test"),
]

websocket_urlpatterns = [
    path("ws/reverie/", views.ReverieConsumer.as_asgi())
]
