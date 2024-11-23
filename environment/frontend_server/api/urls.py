from django.urls import path, re_path

from . import views

app_name = "api"

urlpatterns = [
    path("", views.help, name="main"),
    re_path(r"^help/?$", views.help, name="help"),
    re_path(r"^running/?$", views.getRunningInfo, name="running_info"),

    re_path(r"^pens/?$", views.getPens, name="pens"),
    re_path(r"^pens/(?P<pen_code>[\w-]+)/?$", views.getPen, name="pen"),
    re_path(r"^pens/(?P<pen_code>[\w-]+)/-1/?$", views.getAllSteps, name="all_steps"),
    re_path(r"^pens/(?P<pen_code>[\w-]+)/(?P<step>\d+)/?$", views.getNextStep, name="next_step"),
    re_path(r"^pens/(?P<pen_code>[\w-]+)/payloads/?$", views.getAllPayloads, name="payloads"),
    re_path(r"^pens/(?P<pen_code>[\w-]+)/patches/?$", views.getAllPatches, name="patches"),
    re_path(r"^pens/(?P<pen_code>[\w-]+)/best/?$", views.getAllBestPatches, name="best_patches"),

    re_path(r"^charts/?$", views.getCharts, name="charts"),
    re_path(r"^charts/pens/?$", views.getPenCharts, name="pen_charts"),
    re_path(r"^charts/pens/(?P<pen_code>[\w-]+)/?$", views.getPenChart, name="pen_chart"),
    re_path(r"^charts/urls/?$", views.getUrlCharts, name="url_charts"),
    re_path(r"^charts/attacks/?$", views.getAttackCharts, name="attack_charts"),
    re_path(r"^charts/attacks/(?P<attack>[\w-]+)/?$", views.getAttackChart, name="attack_chart"),

    re_path("", views.not_found),
]
