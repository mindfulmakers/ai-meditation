from config.serializers import BaseModelSerializer

from .models import ContactSubmission


class ContactSubmissionSerializer(BaseModelSerializer):
    class Meta:
        model = ContactSubmission
        fields = ["name", "email", "message", "site_id"]
        read_only_fields = ["site_id"]
