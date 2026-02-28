from rest_framework import generics
from rest_framework.permissions import AllowAny

from contact import serializers
from sites.utils import get_or_create_current_site


class SubmitContactView(generics.CreateAPIView):
    serializer_class = serializers.ContactSubmissionSerializer
    queryset = serializers.ContactSubmission.objects.all()
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        site = get_or_create_current_site(self.request)
        serializer.save(site=site)
