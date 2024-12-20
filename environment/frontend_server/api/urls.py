from django.urls import path, re_path

from . import views

app_name = "api"

urlpatterns = [
    path("", views.help, name="main"),
    re_path(r"^help/?$", views.help, name="help"),
    re_path(r"^running/?$", views.getRunningInfo, name="running_info"),

    re_path(r"^pens/?$", views.getPens, name="pens"),
    re_path(r"^pens/(?P<pen_code>[\w-]+)/?$", views.getPen, name="pen"),
    re_path(r"^pens/(?P<pen_code>[\w-]+)/spawns?/?$", views.getAllSpawns, name="spawn"),
    re_path(r"^pens/(?P<pen_code>[\w-]+)/-1/?$", views.getAllSteps, name="all_steps"),
    re_path(r"^pens/(?P<pen_code>[\w-]+)/(?P<step>\d+)/?$", views.getNextStep, name="next_step"),
    re_path(r"^pens/(?P<pen_code>[\w-]+)/datas?(?:/(?P<step>\d+))?/?$", views.getDatas, name="datas"),
    re_path(r"^pens/(?P<pen_code>[\w-]+)/movements?(?:/(?P<step>\d+))?/?$", views.getMovements, name="movements"),
    re_path(r"^pens/(?P<pen_code>[\w-]+)/pronunciation(?:/(?P<step>\d+))?/?$", views.getPronunciation, name="pronunciation"),
    re_path(r"^pens/(?P<pen_code>[\w-]+)/descriptions?(?:/(?P<step>\d+))?/?$", views.getDescriptions, name="descriptions"),
    re_path(r"^pens/(?P<pen_code>[\w-]+)/chats?(?:/(?P<step>\d+))?/?$", views.getChats, name="chats"),
    re_path(r"^pens/(?P<pen_code>[\w-]+)/payloads?(?:/(?P<step>\d+))?/?$", views.getPayloads, name="payloads"),
    re_path(r"^pens/(?P<pen_code>[\w-]+)/vulnerabilit(y|ies)(?:/(?P<step>\d+))?/?$", views.getVulnerabilities, name="vulnerabilities"),
    re_path(r"^pens/(?P<pen_code>[\w-]+)/patch(es)?(?:/(?P<step>\d+))?/?$", views.getPatches, name="patches"),
    re_path(r"^pens/(?P<pen_code>[\w-]+)/best(?:/(?P<step>\d+))?/?$", views.getBest, name="best"),
    re_path(r"^pens/(?P<pen_code>[\w-]+)/files?/?$", views.getVulnerableFiles, name="vulnerable_files"),

    re_path(r"^charts/?$", views.getCharts, name="charts"),
    re_path(r"^charts/pens/?$", views.getPenCharts, name="pen_charts"),
    re_path(r"^charts/pens/(?P<pen_code>[\w-]+)/?$", views.getPenChart, name="pen_chart"),
    re_path(r"^charts/urls/?$", views.getUrlCharts, name="url_charts"),
    re_path(r"^charts/attacks/?$", views.getAttackCharts, name="attack_charts"),
    re_path(r"^charts/attacks/(?P<attack>[\w-]+)/?$", views.getAttackChart, name="attack_chart"),

    re_path("", views.not_found),
]
