from rest_framework import routers

from burj.views import AccountViewSet

router = routers.DefaultRouter()
router.register(r'accounts', AccountViewSet, base_name='account')
