from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import GetTokenView, SignUpView, UserViewSet

router = DefaultRouter()
router.register('users', UserViewSet, basename='users')

urlpatterns = [
    path('auth/signup/', SignUpView.as_view(), name='signup'),
    path('auth/token/', GetTokenView.as_view(), name='token'),
    path('', include(router.urls)),
]
