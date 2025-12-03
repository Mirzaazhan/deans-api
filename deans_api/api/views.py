from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, permissions, mixins, generics, status
from rest_framework.response import Response
from django.contrib.auth.models import User
from .permissions import NotAllowed
from .models import Crisis, CrisisAssistance, CrisisType, SiteSettings, EmergencyAgencies
from .serializer import (
                CrisisSerializer, 
                CrisisAssistanceSerializer, 
                CrisisTypeSerializer, 
                CrisisUpdateSerializer, 
                CrisisBasicSerializer, 
                UserSerializer, 
                UserAdminSerializer,
                SiteSettingsSerializer,
                EmergencyAgenciesSerializer,
                EmergencyAgenciesUpdateSerializer
            )

from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAdminUser,
    IsAuthenticatedOrReadOnly,
)

# import channels.layers
# from asgiref.sync import async_to_sync

'''
    The View Classes here implements the V-view in the MVC architecture.
    CrisisView, CrisisUpdateView, CrisisPartialUpdateView, 
    CrisisAssistanceView, CrisisTypeView, 
    UserView, UserPartialUpdateView,
    SiteSettingView,
    EmergencyView, EmergencyPartialUpdateView
    
    will all be handled by an api url in urls.py
'''


# =============================================================================
# PERMISSION MIXINS (Reengineered to eliminate code duplication)
# =============================================================================

class PublicReadAdminWriteMixin:
    """
    A reusable permission mixin that provides a common permission pattern:
    - list, retrieve, create: AllowAny (public access)
    - update, partial_update, destroy: IsAdminUser (admin-only access)
    
    This mixin eliminates duplicated get_permissions() logic across multiple
    ViewSet classes, following the DRY (Don't Repeat Yourself) principle.
    
    Usage:
        class MyViewSet(PublicReadAdminWriteMixin, viewsets.ModelViewSet):
            queryset = MyModel.objects.all()
            serializer_class = MySerializer
    """
    
    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        
        Permission Policy:
            - 'list': AllowAny - Anyone can view the list of resources
            - 'retrieve': AllowAny - Anyone can view individual resources
            - 'create': AllowAny - Anyone can create new resources
            - 'update'/'partial_update'/'destroy': IsAdminUser - Only admins can modify/delete
        
        Returns:
            list: A list of instantiated permission objects
        """
        if self.action in ['list', 'retrieve', 'create']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]


class AdminOnlyMixin:
    """
    A reusable permission mixin for ViewSets that require full admin access.
    All actions (list, create, retrieve, update, delete) require admin privileges,
    with all other actions completely blocked.
    
    This mixin is designed for sensitive resources like User management where
    no public access should be permitted.
    
    Usage:
        class MyAdminViewSet(AdminOnlyMixin, viewsets.ModelViewSet):
            queryset = MyModel.objects.all()
            serializer_class = MySerializer
    """
    
    def get_permissions(self):
        """
        Instantiates and returns admin-only permissions for list/create,
        and blocks all other actions.
        
        Permission Policy:
            - 'list': IsAdminUser - Only admins can view user list
            - 'create': IsAdminUser - Only admins can create users
            - All other actions: NotAllowed - Completely blocked
        
        Returns:
            list: A list of instantiated permission objects
        """
        if self.action in ['list', 'create']:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [NotAllowed]
        return [permission() for permission in permission_classes]


# =============================================================================
# VIEWSETS
# =============================================================================

class CrisisViewSet(PublicReadAdminWriteMixin, viewsets.ModelViewSet):
    """
    ViewSet for managing Crisis resources.
    
    Provides CRUD operations for crisis reports in the system.
    Public users can view and create crisis reports, while only
    administrators can update or delete them.
    
    Endpoints:
        GET /crises/ - List all crises
        POST /crises/ - Create a new crisis
        GET /crises/{id}/ - Retrieve a specific crisis
        PUT /crises/{id}/ - Update a crisis (admin only)
        PATCH /crises/{id}/ - Partial update a crisis (admin only)
        DELETE /crises/{id}/ - Delete a crisis (admin only)
    
    Permissions:
        - list, retrieve, create: AllowAny
        - update, partial_update, destroy: IsAdminUser
    """
    queryset = Crisis.objects.all()
    serializer_class = CrisisSerializer
    # def get_serializer_class(self):
    #     if self.request.user.is_staff:
    #         return CrisisSerializer
    #     return CrisisBasicSerializer

class CrisisUpdateView(generics.GenericAPIView, mixins.UpdateModelMixin):
    """
    API endpoint for full updates to Crisis resources.
    
    Requires submitting all required fields for the update.
    Uses PUT method for complete resource replacement.
    
    Endpoint:
        PUT /crises/update/{pk}/ - Full update of a crisis
    """
    queryset = Crisis.objects.all()
    serializer_class = CrisisSerializer

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)


class CrisisPartialUpdateView(generics.GenericAPIView, mixins.UpdateModelMixin):
    """
    API endpoint for partial updates to Crisis resources.
    
    Only the fields that need to be modified should be provided.
    Uses PUT method for partial resource modification.
    
    Endpoint:
        PUT /crises/update-partial/{pk}/ - Partial update of a crisis
    """
    queryset = Crisis.objects.all()
    serializer_class = CrisisSerializer

    def put(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)


class CrisisAssistanceViewSet(PublicReadAdminWriteMixin, viewsets.ModelViewSet):
    """
    ViewSet for managing Crisis Assistance types.
    
    Provides CRUD operations for assistance categories that can be
    requested during a crisis (e.g., Medical, Fire, Police).
    
    Endpoints:
        GET /crisisassistance/ - List all assistance types
        POST /crisisassistance/ - Create a new assistance type
        GET /crisisassistance/{id}/ - Retrieve a specific assistance type
        PUT /crisisassistance/{id}/ - Update an assistance type (admin only)
        PATCH /crisisassistance/{id}/ - Partial update (admin only)
        DELETE /crisisassistance/{id}/ - Delete an assistance type (admin only)
    
    Permissions:
        - list, retrieve, create: AllowAny
        - update, partial_update, destroy: IsAdminUser
    """
    queryset = CrisisAssistance.objects.all()
    serializer_class = CrisisAssistanceSerializer


class CrisisTypeViewSet(PublicReadAdminWriteMixin, viewsets.ModelViewSet):
    """
    ViewSet for managing Crisis Type categories.
    
    Provides CRUD operations for crisis type classifications
    (e.g., Natural Disaster, Fire, Accident, etc.).
    
    Endpoints:
        GET /crisistype/ - List all crisis types
        POST /crisistype/ - Create a new crisis type
        GET /crisistype/{id}/ - Retrieve a specific crisis type
        PUT /crisistype/{id}/ - Update a crisis type (admin only)
        PATCH /crisistype/{id}/ - Partial update (admin only)
        DELETE /crisistype/{id}/ - Delete a crisis type (admin only)
    
    Permissions:
        - list, retrieve, create: AllowAny
        - update, partial_update, destroy: IsAdminUser
    """
    queryset = CrisisType.objects.all()
    serializer_class = CrisisTypeSerializer


class UserViewSet(AdminOnlyMixin, viewsets.ModelViewSet):
    """
    ViewSet for managing User accounts.
    
    Provides restricted CRUD operations for system users.
    All operations require administrator privileges for security.
    
    Endpoints:
        GET /users/ - List all users (admin only)
        POST /users/ - Create a new user (admin only)
        Other actions are blocked for security
    
    Permissions:
        - list, create: IsAdminUser
        - retrieve, update, partial_update, destroy: NotAllowed
    """
    serializer_class = UserSerializer
    queryset = User.objects.all()

    # def get_serializer_class(self):
    #     if self.request.user.is_staff:
    #         return UserAdminSerializer
    #     return UserSerializer


class UserPartialUpdateView(generics.GenericAPIView, mixins.UpdateModelMixin):
    """
    API endpoint for partial updates to User accounts.
    
    Allows administrators to update specific user fields without
    providing all user data. Requires admin authentication.
    
    Endpoint:
        PUT /users/update-partial/{pk}/ - Partial update of a user (admin only)
    
    Permissions:
        IsAdminUser - Only administrators can modify user accounts
    """
    queryset = User.objects.all()
    serializer_class = UserAdminSerializer
    permission_classes = (IsAdminUser,)

    def put(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)


class SiteSettingViewSet(PublicReadAdminWriteMixin, viewsets.ModelViewSet):
    """
    ViewSet for managing Site Settings (Singleton pattern).
    
    Provides access to system-wide configuration settings including
    social media credentials and reporting email addresses.
    
    Note: This model uses the Singleton pattern - only one instance exists.
    
    Endpoints:
        GET /sitesettings/ - List site settings
        POST /sitesettings/ - Create settings (if not exists)
        GET /sitesettings/{id}/ - Retrieve settings
        PUT /sitesettings/{id}/ - Update settings (admin only)
        PATCH /sitesettings/{id}/ - Partial update (admin only)
        DELETE /sitesettings/{id}/ - Delete settings (admin only)
    
    Permissions:
        - list, retrieve, create: AllowAny
        - update, partial_update, destroy: IsAdminUser
    """
    serializer_class = SiteSettingsSerializer
    queryset = SiteSettings.objects.all()


class EmergencyAgenciesView(PublicReadAdminWriteMixin, viewsets.ModelViewSet):
    """
    ViewSet for managing Emergency Agencies.
    
    Provides CRUD operations for emergency agency contact information
    (e.g., Police, Fire Department, Ambulance services).
    
    Endpoints:
        GET /emergencyagencies/ - List all emergency agencies
        POST /emergencyagencies/ - Create a new agency
        GET /emergencyagencies/{id}/ - Retrieve a specific agency
        PUT /emergencyagencies/{id}/ - Update an agency (admin only)
        PATCH /emergencyagencies/{id}/ - Partial update (admin only)
        DELETE /emergencyagencies/{id}/ - Delete an agency (admin only)
    
    Permissions:
        - list, retrieve, create: AllowAny
        - update, partial_update, destroy: IsAdminUser
    """
    serializer_class = EmergencyAgenciesSerializer
    queryset = EmergencyAgencies.objects.all()


class EmergencyAgenciesPartialUpdateView(generics.GenericAPIView, mixins.UpdateModelMixin):
    """
    API endpoint for partial updates to Emergency Agencies.
    
    Allows modification of specific agency fields without
    providing all agency data.
    
    Endpoint:
        PUT /emergencyagencies/update-partial/{pk}/ - Partial update of an agency
        DELETE /emergencyagencies/update-partial/{pk}/ - Delete an agency
    """
    serializer_class = EmergencyAgenciesUpdateSerializer
    queryset = EmergencyAgencies.objects.all()

    def put(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    def delete(self, request, pk, format=None):
        event = self.get_object(pk)
        event.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)