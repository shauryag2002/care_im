from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema

from care_im.api.serializers.im import HelloSerializer
from care_im.models.im import Hello
from care_im.utils.whatsapp_client import WhatsAppClient
from django.http import HttpResponse
import logging
logger = logging.getLogger(__name__)


class InstantMessageViewSet(
    viewsets.ViewSet
):
    queryset = Hello.objects.all().order_by("-created_date")
    serializer_class = HelloSerializer
    lookup_field = "external_id"
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["instant-messaging"],
        description="Handle WhatsApp webhook verification and incoming messages"
    )
    @action(detail=False, methods=["GET", "POST"])
    def webhook(self, request):
        """Handle webhook verification and incoming messages"""
        client = WhatsAppClient()

        # Handle webhook verification
        if request.method == "GET":
            mode = request.GET.get('hub.mode', '')
            token = request.GET.get('hub.verify_token', '')
            challenge = request.GET.get('hub.challenge', '')

            logger.info(f"Webhook verification request - Mode: {mode}, Token: {token}")

            if mode == 'subscribe' and client.verify_webhook(token):
                logger.info("Webhook verification successful")
                return HttpResponse(challenge, content_type='text/plain')

            logger.error("Webhook verification failed")
            return HttpResponse('Forbidden', status=403)

        # Handle incoming messages
        try:
            client.process_webhook_event(request.data)
            return Response({'status': 'success'})
        except Exception as e:
            logger.error(f"Error processing webhook event: {str(e)}")
            return Response(
                {'status': 'error', 'message': str(e)},
                status=400
            )
