from django.urls import path, re_path

from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),

    path("live/", views.live, name="live"),
    re_path(r"^simulator/(?:(?P<sim_code>[\w-]+)/)?(?:(?P<step>\d+)/)?(?:(?P<speed>\d+)/)?$", views.simulator, name="simulator"),
    re_path(r'^replay_persona_state/(?P<sim_code>[\w-]+)/(?P<step>[\w-]+)/(?P<persona_name>[\w-]+)/$', views.replay_persona_state, name='replay_persona_state'),

    re_path(r"^process_environment/$", views.process_environment, name="process_environment"),
    re_path(r"^update_environment/$", views.update_environment, name="update_environment"),
    re_path(r"^path_tester_update/$", views.path_tester_update, name="path_tester_update"),
]
