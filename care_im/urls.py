from rest_framework.routers import DefaultRouter

from care_im.api.viewsets.im import InstantMessageViewSet

router = DefaultRouter()

router.register("", InstantMessageViewSet, basename="instant-messaging")

urlpatterns = router.urls
