from django.urls import path

from . import views

urlpatterns = [
    path("signin/", views.signin, name="signin"),
    path("manage/", views.manage, name="manage"),

    path("signout", views.signout, name="signout"),
    path("users", views.user, name="user"),
    path("users/<int:userid>", views.user, name="user_info"),
    path("users/update", views.user_update, name="user_update"),
    path("users/delete", views.user_delete, name="user_delete"),
]
