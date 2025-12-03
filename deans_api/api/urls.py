from django.urls import include, path, re_path
from django.contrib import admin
from rest_framework import routers

from .views import (
    CrisisViewSet,
    CrisisAssistanceViewSet,
    CrisisTypeViewSet,
    CrisisUpdateView,
    CrisisPartialUpdateView,
    UserViewSet,
    UserPartialUpdateView,
    EmergencyAgenciesView,
    EmergencyAgenciesPartialUpdateView,
    SiteSettingViewSet
)

"""
URL Configuration for the API module.

This module defines all API endpoints using Django REST Framework's router
and additional custom URL patterns for update views.

API URL Structure:
    - /crises/                           - Crisis CRUD operations
    - /crises/update/<pk>/               - Full crisis update
    - /crises/update-partial/<pk>/       - Partial crisis update
    - /crisisassistance/                 - Crisis Assistance CRUD
    - /crisistype/                       - Crisis Type CRUD
    - /users/                            - User management (admin only)
    - /users/update-partial/<pk>/        - Partial user update
    - /emergencyagencies/                - Emergency Agencies CRUD
    - /emergencyagencies/update-partial/<pk>/ - Partial agency update
    - /sitesettings/                     - Site Settings CRUD

Note: Migrated from deprecated url() to re_path()/path() for Django 4.x compatibility.
"""

# =============================================================================
# ROUTER CONFIGURATION
# =============================================================================
# Using DefaultRouter for automatic URL routing of ViewSets
# Note: Router prefixes should not start with '^' when using path-style routing
# Note: Using 'base_name' instead of 'basename' for DRF 3.8.x compatibility

router = routers.DefaultRouter()
router.register(r'crises', CrisisViewSet, base_name='crisis')
router.register(r'crisisassistance', CrisisAssistanceViewSet, base_name='crisisassistance')
router.register(r'crisistype', CrisisTypeViewSet, base_name='crisistype')
router.register(r'users', UserViewSet, base_name='user')
router.register(r'emergencyagencies', EmergencyAgenciesView, base_name='emergencyagency')
router.register(r'sitesettings', SiteSettingViewSet, base_name='sitesetting')


# =============================================================================
# URL PATTERNS
# =============================================================================
# App namespace for URL reversing (e.g., 'api:crisis_update')
app_name = 'api'

urlpatterns = [
    # Authentication endpoints
    path('api-auth/', include('rest_framework.urls')),
    path('rest-auth/', include('rest_auth.urls')),
    
    # Router-generated URLs (ViewSet CRUD endpoints)
    path('', include(router.urls)),
    
    # Custom update endpoints using path() with type converters
    # These provide alternative update mechanisms outside the ViewSet
    path('crises/update/<int:pk>/', CrisisUpdateView.as_view(), name='crisis_update'),
    path('crises/update-partial/<int:pk>/', CrisisPartialUpdateView.as_view(), name='crisis_partial_update'),
    path('users/update-partial/<int:pk>/', UserPartialUpdateView.as_view(), name='user_partial_update'),
    path('emergencyagencies/update-partial/<int:pk>/', EmergencyAgenciesPartialUpdateView.as_view(), name='emergencyagency_partial_update'),
]

# =============================================================================
# DEPRECATED PATTERNS (Kept for reference)
# =============================================================================
# The following patterns used the deprecated url() function:
# url(r'^crises/update/(?P<pk>\d+)/$', ...) -> path('crises/update/<int:pk>/', ...)
# 
# Registration with rest auth (if needed):
# path('rest-auth/registration/', include('rest_auth.registration.urls')),,