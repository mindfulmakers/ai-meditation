from __future__ import annotations

from django.urls import path

from . import views

urlpatterns = [
    path("users/me/", views.UserDetail.as_view(), name="user-detail"),
    path("apns/", views.APNSView.as_view(), name="apns"),
    path("users/me/delete/", views.DeleteUserView.as_view(), name="delete-user"),
]
