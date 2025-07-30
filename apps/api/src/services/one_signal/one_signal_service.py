import onesignal
from onesignal.api import default_api
from onesignal.model.create_notification_success_response import CreateNotificationSuccessResponse
from onesignal.model.notification import Notification

from src.settings import settings


class OneSignalService:
    def __init__(self):
        self.configuration = onesignal.Configuration(
            app_key=settings.ONESIGNAL_API_KEY,
        )

    async def send_notification(self, notification: Notification | None = None) -> CreateNotificationSuccessResponse:
        with onesignal.ApiClient(self.configuration) as api_client:
            api_instance = default_api.DefaultApi(api_client)
            return api_instance.create_notification(notification)

    async def get_notifications(self):
        with onesignal.ApiClient(self.configuration) as api_client:
            api_instance = default_api.DefaultApi(api_client)
            return api_instance.get_notifications(settings.ONESIGNAL_APPERTO_APP_ID)
