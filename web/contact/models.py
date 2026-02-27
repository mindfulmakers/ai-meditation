from django.contrib.sites.models import Site
from django.db import models


# Create your models here.
class ContactSubmission(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True)
    site = models.ForeignKey(Site, on_delete=models.SET_NULL, null=True, blank=True)
    email = models.EmailField()
    message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email
