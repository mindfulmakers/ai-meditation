from rest_framework import generics
from rest_framework.permissions import AllowAny

from django.contrib.sites.shortcuts import get_current_site
from contact import serializers


class SubmitContactView(generics.CreateAPIView):
    serializer_class = serializers.ContactSubmissionSerializer
    queryset = serializers.ContactSubmission.objects.all()
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        site = get_current_site(self.request)
        serializer.save(site=site)
