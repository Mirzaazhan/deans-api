from django.contrib.auth.models import User 
from django.db import models
from .CrisisType import CrisisType
from .Operator import Operator
from .CrisisAssistance import CrisisAssistance
from django.db.models import signals
from datetime import datetime, timedelta
import json
import logging

logger = logging.getLogger(__name__)

STATUS_CHOICES = (
    ('PD', 'Pending'),
    ('DP', 'Dispatched'),
    ('RS', 'Resolved'),
)
'''
    This is the most important model of the whole CMS System. The Crisis Model consists of all the information that a crisis needs.
    Details:
        reporter's name,  String
        reporter's mobile_number, String
        crisis_id, String
        crisis_type, Many to many field linked to CrisisType Model
        crisis_description, longer String, Text Field
        crisis_assistance, Many to many field linked to CrisisAssistance Model
        crisis_assistance_description, longer string, Text Field
        crisis_time, a date time field
        crisis_location1&2, longer String, Text field
        updated_at, a date time field records last object modification
        owner, a Many to many field linked to User Model
        visible, a boolean field recording the visibility of a crisis in the front end
        dispatch_trigger, a boolean field recording the signal of a dispatch action
        crisis status, a tuple recording the crisis status
'''
class Crisis(models.Model):
    your_name = models.CharField(default=None,max_length=255)
    mobile_number = models.CharField(default=None,max_length=255)
    crisis_id = models.AutoField(primary_key=True)
    crisis_type = models.ManyToManyField(CrisisType)
    crisis_description = models.TextField(default="")
    crisis_assistance = models.ManyToManyField(CrisisAssistance)
    crisis_assistance_description = models.TextField(default="")
    crisis_time = models.DateTimeField(auto_now_add=True)
    crisis_location1 = models.TextField()
    crisis_location2 = models.TextField(default="")
    updated_at = models.DateTimeField(auto_now_add=True)
    owner = models.ManyToManyField(User)
    visible = models.BooleanField(default=True)
    phone_number_to_notify = models.CharField(default="",max_length=255)
    dispatch_trigger = models.BooleanField(default=False)

    crisis_status = models.CharField(choices=STATUS_CHOICES, default='PD',  max_length=254)

    def __str__(self):
        return str(self.crisis_id)

    class Meta:
        ordering = ['-crisis_id']


'''
    Signal handler for Crisis model post_save events.
    
    This handler is responsible for:
    1. Sending social media notifications (Facebook, Twitter)
    2. Sending dispatch notifications (SMS/WhatsApp) when crisis is dispatched
    3. Broadcasting WebSocket updates to connected clients
    
    Reengineered to use service layer for better separation of concerns,
    error handling, and maintainability.
'''
def trigger(sender, instance, created, **kwargs):
    """
    Signal handler triggered when a Crisis instance is saved.
    
    Uses notification and WebSocket services to handle all communication
    with proper error handling and logging.
    """
    from ..services.notification_service import NotificationService
    from ..services.websocket_service import WebSocketService
    
    # Initialize services
    notification_service = NotificationService()
    websocket_service = WebSocketService()
    
    # Get the crisis instance (ensure we have the latest from DB)
    try:
        crisis = Crisis.objects.select_related().prefetch_related(
            'crisis_type', 'crisis_assistance'
        ).get(pk=instance.pk)
    except Crisis.DoesNotExist:
        logger.error(f"Crisis {instance.pk} not found after save signal")
        return
    
    # 1. Send social media notifications
    try:
        logger.info(f"Processing social media notification for crisis {crisis.crisis_id}")
        
        # Get related crises for social media payload
        created_time = datetime.now() - timedelta(minutes=30)
        recent_resolved_crises = Crisis.objects.filter(
            updated_at__gte=created_time,
            crisis_status="RS"
        ).prefetch_related('crisis_type', 'crisis_assistance')
        
        active_crises = Crisis.objects.exclude(
            crisis_status="RS"
        ).prefetch_related('crisis_type', 'crisis_assistance')
        
        # Send social media notification
        notification_service.send_social_media_notification(
            crisis,
            recent_resolved_crises,
            active_crises
        )
        
    except Exception as e:
        logger.error(
            f"Failed to send social media notification for crisis {crisis.crisis_id}: {str(e)}",
            exc_info=True
        )
        # Continue processing - don't let social media failure block other operations
    
    # 2. Send dispatch notifications if crisis is dispatched
    if crisis.crisis_status == "DP" and crisis.dispatch_trigger:
        try:
            logger.info(f"Processing dispatch notification for crisis {crisis.crisis_id}")
            
            # Parse phone numbers
            if crisis.phone_number_to_notify:
                try:
                    phone_numbers = json.loads(crisis.phone_number_to_notify)
                    if isinstance(phone_numbers, list):
                        successful, failed = notification_service.send_dispatch_notification(
                            crisis,
                            phone_numbers
                        )
                        logger.info(
                            f"Dispatch notifications for crisis {crisis.crisis_id}: "
                            f"{successful} successful, {failed} failed"
                        )
                    else:
                        logger.warning(
                            f"Invalid phone_numbers format for crisis {crisis.crisis_id}: "
                            f"expected list, got {type(phone_numbers)}"
                        )
                except json.JSONDecodeError as e:
                    logger.error(
                        f"Failed to parse phone_numbers JSON for crisis {crisis.crisis_id}: {str(e)}"
                    )
            else:
                logger.warning(
                    f"No phone numbers to notify for dispatched crisis {crisis.crisis_id}"
                )
                
        except Exception as e:
            logger.error(
                f"Failed to send dispatch notification for crisis {crisis.crisis_id}: {str(e)}",
                exc_info=True
            )
            # Continue processing - don't let dispatch failure block WebSocket updates
    
    # 3. Broadcast WebSocket update
    try:
        logger.info(f"Broadcasting WebSocket update for crisis {crisis.crisis_id}")
        
        # Optimize query: only fetch visible crises and use prefetch for related objects
        all_crises = Crisis.objects.filter(visible=True).prefetch_related(
            'crisis_type', 'crisis_assistance'
        )
        
        websocket_service.broadcast_crises_update(all_crises)
        
    except Exception as e:
        logger.error(
            f"Failed to broadcast WebSocket update for crisis {crisis.crisis_id}: {str(e)}",
            exc_info=True
        )
        # This is critical but we don't want to break the save operation
        # The error is logged for monitoring and debugging

signals.post_save.connect(receiver=trigger, sender=Crisis)

