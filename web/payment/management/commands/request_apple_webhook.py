from django.conf import settings
from django.core.management import BaseCommand

from appstoreserverlibrary.api_client import AppStoreServerAPIClient, APIException
from appstoreserverlibrary.models.Environment import Environment


class Command(BaseCommand):
    help = "Request Apple webhook for debugging"

    def handle(self, *args, **options):

        key_id = settings.APPLE_STOREKIT_KEY_ID
        issuer_id = settings.APPLE_STOREKIT_ISSUER_ID
        bundle_id = settings.APPLE_BUNDLE_ID
        environment = Environment.PRODUCTION

        client = AppStoreServerAPIClient(
            settings.APPLE_STOREKIT_P8_CONTENTS.encode(), key_id, issuer_id, bundle_id, environment
        )

        try:
            response = client.request_test_notification()
            print(response)
        except APIException as e:
            print(e)
