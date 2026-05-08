from django.urls import re_path
from dashboard import consumers

websocket_urlpatterns = [
    re_path(r'ws/posture/$', consumers.PostureConsumer.as_asgi()),
]