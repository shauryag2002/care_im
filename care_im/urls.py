from rest_framework.routers import DefaultRouter

from care_im.api.viewsets.im import HelloViewset

router = DefaultRouter()

router.register("care_im", HelloViewset, basename="hello__hello")

urlpatterns = router.urls
