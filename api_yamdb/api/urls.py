from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import (CategoryViewSet, GenreViewSet, TitleViewSet,
                       CommentViewSet, ReviewViewSet, GetTokenView, 
                       SignUpView, UserViewSet
                    )
# from users.views import GetTokenView, SignUpView, UserViewSet

router_v1 = DefaultRouter()
router_v1.register(r'categories', CategoryViewSet, basename='categories')
router_v1.register(r'genres', GenreViewSet, basename='genres')
router_v1.register(r'titles', TitleViewSet, basename='titles')
router_v1.register(r'users', UserViewSet, basename='users')
router_v1.register(
    r'titles\/(?P<title_id>\d+)\/reviews', ReviewViewSet, basename='reviews',
)
router_v1.register(
    r'titles\/(?P<title_id>\d+)\/reviews/(?P<review_id>\d+)\/comments',
    CommentViewSet,
    basename='comments',
)

urlpatterns = [
    path('v1/', include([
        path('auth/signup/', SignUpView.as_view(), name='signup'),
        path('auth/token/', GetTokenView.as_view(), name='token'),
        path('', include(router_v1.urls)),
    ])),
]
