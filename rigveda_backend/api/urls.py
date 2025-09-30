from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EntityViewSet, RelationshipViewSet, StatsViewSet

router = DefaultRouter()
router.register(r'entities', EntityViewSet, basename='entity')
router.register(r'relationships', RelationshipViewSet, basename='relationship')
router.register(r'stats', StatsViewSet, basename='stats')

urlpatterns = [
    path('', include(router.urls)),
]
