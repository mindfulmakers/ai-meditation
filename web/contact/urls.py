from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from contact import views

urlpatterns = [
    path("contact/", csrf_exempt(views.SubmitContactView.as_view()), name="contact"),
]
