from __future__ import annotations

import logging
import os
import time

import httpx
import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from sendgrid import Mail, SendGridAPIClient
from twilio.rest import Client

from config.taskiq_config import broker
from users.models import UserAPNSToken

required_prefix = "From your assistant: "


logger = logging.getLogger(__name__)


User = get_user_model()


@broker.task
def send_email(subject, message, to_email):
    message = Mail(
        from_email=f"app@{settings.DOMAIN_NAME}",
        to_emails=to_email,
        subject=subject,
        html_content=message,
    )
    sg = SendGridAPIClient(os.environ.get("SENDGRID_API_KEY"))
    response = sg.send(message)
    assert response.status_code in (202, 200)


@broker.task
def send_sms(message, to_number):
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    client.messages.create(
        to=to_number, from_=settings.OWNED_TWILIO_NUMBER, body=required_prefix + message
    )


@broker.task
async def send_apn(user_id, message, data: dict | None = None):
    user = await User.objects.aget(id=user_id)
    token_instance = await UserAPNSToken.objects.filter(user=user).afirst()
    if not token_instance:
        return
    token = token_instance.token
    team_id = settings.NOTIFICATIONS_APPLE_TEAM_ID
    bundle_id = settings.APPLE_BUNDLE_ID
    auth_key_id = settings.NOTIFICATIONS_APPLE_AUTH_KEY_ID
    # APNs URL for push notifications (use the appropriate server: development or production)
    apns_url_template = (
        "https://api.push.apple.com:443/3/device/{}"
        if not settings.NOTIFICATIONS_SANDBOX
        else "https://api.sandbox.push.apple.com:443/3/device/{}"
    )
    apns_url = apns_url_template.format(token)
    # Generate the JWT token for authentication
    token_headers = {"alg": "ES256", "kid": auth_key_id}
    token_payload = {"iss": team_id, "iat": time.time()}
    auth_key = settings.NOTIFICATIONS_APPLE_P8_CONTENTS
    jwt_token = jwt.encode(
        payload=token_payload, key=auth_key, algorithm="ES256", headers=token_headers
    )
    # Prepare request headers
    request_headers = {
        "apns-expiration": "0",
        "apns-priority": "10",
        "apns-topic": bundle_id,
        "authorization": "bearer " + jwt_token,
    }
    payload = {
        "aps": {
            "alert": message,
            "sound": "default",
        },
    }
    # Add custom data to payload if provided
    if data:
        payload.update(data)
    # Send the notification
    async with httpx.AsyncClient(http2=True) as client:
        response = await client.post(apns_url, json=payload, headers=request_headers)
    if response.status_code >= 400:
        logger.error(f"Could not send APN: {response.content}")
