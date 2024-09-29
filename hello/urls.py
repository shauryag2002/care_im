from rest_framework.routers import DefaultRouter

from hello.api.viewsets.hello import HelloViewset

router = DefaultRouter()

router.register("hello", HelloViewset, basename="hello__hello")

urlpatterns = router.urls
