from django.urls import path

from . import views

urlpatterns = [
    path("signin/", views.signin, name="signin"),
    path("manage/", views.manage, name="manage"),

    path("signout", views.signout, name="signout"),
    path("user", views.user, name="user"),
    path("user/update", views.user_update, name="user_update"),
    path("user/delete", views.user_delete, name="user_delete"),
]
