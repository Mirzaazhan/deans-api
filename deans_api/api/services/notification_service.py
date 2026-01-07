"""
Notification Service for Crisis Management System

This service handles all notification-related operations including:
- Social media notifications (Facebook, Twitter)
- SMS/WhatsApp dispatch notifications
- Error handling and retry logic
- Request validation

Written as part of reengineering task to improve code quality and maintainability.
"""
import json
import logging
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

import requests
from django.conf import settings
from django.db.models import QuerySet

logger = logging.getLogger(__name__)


class NotificationServiceError(Exception):
    """Base exception for notification service errors."""
    pass


class NotificationRequestError(NotificationServiceError):
    """Raised when HTTP request fails."""
    pass


class NotificationTimeoutError(NotificationServiceError):
    """Raised when request times out."""
    pass


class NotificationService:
    """
    Service class for handling crisis notifications.
    
    Provides methods for sending social media notifications and dispatch notices
    with proper error handling, retry logic, and request validation.
    """
    
    def __init__(self):
        """Initialize notification service with configuration from settings."""
        self.social_messages_url = getattr(
            settings, 
            'NOTIFICATION_SOCIAL_MESSAGES_URL', 
            'http://notification:8000/socialmessages/'
        )
        self.dispatch_notices_url = getattr(
            settings,
            'NOTIFICATION_DISPATCH_NOTICES_URL',
            'http://notification:8000/dispatchnotices/'
        )
        self.request_timeout = getattr(settings, 'NOTIFICATION_REQUEST_TIMEOUT', 10)
        self.max_retries = getattr(settings, 'NOTIFICATION_MAX_RETRIES', 3)
        self.retry_delay = getattr(settings, 'NOTIFICATION_RETRY_DELAY', 1)  # seconds
        self.deans_url = getattr(settings, 'DEANS_URL', 'https://deans.csming.com/')
        self.shelter_url = getattr(settings, 'SHELTER_URL', 'https://deans.csming.com/')
    
    def _make_request_with_retry(
        self, 
        url: str, 
        payload: Dict, 
        operation_name: str
    ) -> requests.Response:
        """
        Make HTTP request with exponential backoff retry logic.
        
        Args:
            url: The endpoint URL
            payload: JSON payload to send
            operation_name: Name of operation for logging
            
        Returns:
            Response object if successful
            
        Raises:
            NotificationRequestError: If all retries fail
            NotificationTimeoutError: If request times out
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                logger.info(
                    f"Attempting {operation_name} (attempt {attempt + 1}/{self.max_retries})"
                )
                
                response = requests.post(
                    url,
                    json=payload,
                    headers={'content-type': 'application/json'},
                    timeout=self.request_timeout
                )
                
                # Validate response
                response.raise_for_status()
                
                logger.info(
                    f"{operation_name} successful. Status: {response.status_code}"
                )
                return response
                
            except requests.exceptions.Timeout as e:
                last_exception = NotificationTimeoutError(
                    f"{operation_name} timed out after {self.request_timeout}s"
                )
                logger.warning(
                    f"{operation_name} timeout on attempt {attempt + 1}/{self.max_retries}"
                )
                
            except requests.exceptions.RequestException as e:
                last_exception = NotificationRequestError(
                    f"{operation_name} failed: {str(e)}"
                )
                logger.warning(
                    f"{operation_name} failed on attempt {attempt + 1}/{self.max_retries}: {str(e)}"
                )
            
            # Exponential backoff: wait before retry (except on last attempt)
            if attempt < self.max_retries - 1:
                delay = self.retry_delay * (2 ** attempt)
                logger.info(f"Retrying {operation_name} in {delay} seconds...")
                time.sleep(delay)
        
        # All retries failed
        logger.error(f"{operation_name} failed after {self.max_retries} attempts")
        raise last_exception
    
    def format_crisis_data(self, crisis) -> Dict:
        """
        Format crisis data into a standardized dictionary.
        
        Args:
            crisis: Crisis model instance
            
        Returns:
            Dictionary with formatted crisis data
        """
        return {
            "crisis_time": crisis.crisis_time.strftime("%Y-%m-%d %H:%M:%S"),
            "resolved_by": (
                crisis.updated_at.strftime("%Y-%m-%d %H:%M:%S") 
                if crisis.crisis_status == "RS" 
                else "None"
            ),
            "location": crisis.crisis_location1,
            "location2": crisis.crisis_location2,
            "type": ", ".join([ct.name for ct in crisis.crisis_type.all()]),
            "status": crisis.crisis_status,
            "crisis_description": crisis.crisis_description,
            "crisis_assistance": ", ".join([ca.name for ca in crisis.crisis_assistance.all()]),
            "assistance_description": crisis.crisis_assistance_description
        }
    
    def construct_social_media_payload(
        self, 
        crisis, 
        recent_resolved_crises: QuerySet,
        active_crises: QuerySet
    ) -> Dict:
        """
        Construct payload for social media notifications.
        
        Args:
            crisis: The current crisis instance
            recent_resolved_crises: QuerySet of recently resolved crises
            active_crises: QuerySet of active crises
            
        Returns:
            Dictionary containing social media payload
        """
        created_time = datetime.now() - timedelta(minutes=30)
        
        payload = {
            'postTime': created_time.strftime('%Y-%m-%d %H:%M'),
            'deansURL': self.deans_url,
            'shelterURL': self.shelter_url,
            'recent_resolved_crisis': [
                self.format_crisis_data(c) for c in recent_resolved_crises
            ],
            'active_crisis': [
                self.format_crisis_data(c) for c in active_crises
            ],
            'new_crisis': [self.format_crisis_data(crisis)],
        }
        
        # Construct text message for social media
        crisis_types = ", ".join([ct.name for ct in crisis.crisis_type.all()])
        assistance_types = ", ".join([ca.name for ca in crisis.crisis_assistance.all()])
        
        message = "\nWe have received the following crisis report, need your immediate attention:\n\n"
        message += f"Reported Time: {crisis.crisis_time}\n"
        message += f"Location: {crisis.crisis_location1}\n"
        message += f"Location2: {crisis.crisis_location2}\n"
        message += f"Crisis Type: {crisis_types}\n"
        message += f"Crisis Description: {crisis.crisis_description}\n"
        message += f"Requested Assistance: {assistance_types}\n"
        message += f"Assistance Description: {crisis.crisis_assistance_description}\n"
        
        payload['text'] = message
        
        return payload
    
    def construct_twitter_payload(self, social_media_payload: Dict) -> str:
        """
        Construct Twitter-specific message from social media payload.
        
        Args:
            social_media_payload: The social media payload dictionary
            
        Returns:
            Formatted Twitter message string
        """
        twitter_message = f"A Crisis is happening at time: {social_media_payload['postTime']}!\n"
        twitter_message += f"For your safety. Shelter Information: {social_media_payload['shelterURL']}\n"
        twitter_message += f"For Crisis detail information: {social_media_payload['deansURL']}"
        return twitter_message
    
    def construct_dispatch_message(self, crisis) -> str:
        """
        Construct dispatch message for SMS/WhatsApp notifications.
        
        Args:
            crisis: Crisis model instance
            
        Returns:
            Formatted dispatch message string
        """
        crisis_types = ", ".join([ct.name for ct in crisis.crisis_type.all()])
        assistance_types = ", ".join([ca.name for ca in crisis.crisis_assistance.all()])
        
        message = "We have received the following crisis report, need your immediate attention:\n\n"
        message += f"Reported Time: {crisis.crisis_time}\n"
        message += f"Reporter Name: {crisis.your_name}\n"
        message += f"Mobile Number: {crisis.mobile_number}\n"
        message += f"Location: {crisis.crisis_location1}\n"
        message += f"Location2: {crisis.crisis_location2}\n"
        message += f"Crisis Type: {crisis_types}\n"
        message += f"Crisis Description: {crisis.crisis_description}\n"
        message += f"Requested Assistance: {assistance_types}\n"
        message += f"Assistance Description: {crisis.crisis_assistance_description}\n"
        message += "\nThank you for keeping our people safe!"
        
        return message
    
    def send_social_media_notification(
        self, 
        crisis,
        recent_resolved_crises: QuerySet,
        active_crises: QuerySet
    ) -> bool:
        """
        Send social media notifications (Facebook and Twitter).
        
        Args:
            crisis: Crisis model instance
            recent_resolved_crises: QuerySet of recently resolved crises
            active_crises: QuerySet of active crises
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Construct payloads
            fb_payload = self.construct_social_media_payload(
                crisis, 
                recent_resolved_crises, 
                active_crises
            )
            tw_payload = self.construct_twitter_payload(fb_payload)
            
            # Prepare request payload
            request_payload = {
                "message": {
                    "twitterShare": tw_payload,
                    "facebookShare": fb_payload
                }
            }
            
            # Send request with retry logic
            response = self._make_request_with_retry(
                self.social_messages_url,
                request_payload,
                "Social media notification"
            )
            
            logger.info(
                f"Social media notification sent successfully for crisis {crisis.crisis_id}. "
                f"Status: {response.status_code}"
            )
            return True
            
        except NotificationServiceError as e:
            logger.error(
                f"Failed to send social media notification for crisis {crisis.crisis_id}: {str(e)}",
                exc_info=True
            )
            return False
        except Exception as e:
            logger.error(
                f"Unexpected error sending social media notification for crisis {crisis.crisis_id}: {str(e)}",
                exc_info=True
            )
            return False
    
    def send_dispatch_notification(
        self, 
        crisis, 
        phone_numbers: List[str]
    ) -> Tuple[int, int]:
        """
        Send dispatch notifications (SMS/WhatsApp) to multiple phone numbers.
        
        Args:
            crisis: Crisis model instance
            phone_numbers: List of phone numbers to notify
            
        Returns:
            Tuple of (successful_count, failed_count)
        """
        if not phone_numbers:
            logger.warning(f"No phone numbers provided for dispatch notification (crisis {crisis.crisis_id})")
            return (0, 0)
        
        message = self.construct_dispatch_message(crisis)
        successful = 0
        failed = 0
        
        for phone_number in phone_numbers:
            try:
                # Format phone number (add country code if needed)
                if not phone_number.startswith('+'):
                    prefixed_phone_number = f"+65{phone_number}"
                else:
                    prefixed_phone_number = phone_number
                
                request_payload = {
                    "number": prefixed_phone_number,
                    "message": message
                }
                
                # Send request with retry logic
                response = self._make_request_with_retry(
                    self.dispatch_notices_url,
                    request_payload,
                    f"Dispatch notification to {prefixed_phone_number}"
                )
                
                logger.info(
                    f"Dispatch notification sent to {prefixed_phone_number} for crisis {crisis.crisis_id}. "
                    f"Status: {response.status_code}"
                )
                successful += 1
                
            except NotificationServiceError as e:
                logger.error(
                    f"Failed to send dispatch notification to {phone_number} for crisis {crisis.crisis_id}: {str(e)}"
                )
                failed += 1
            except Exception as e:
                logger.error(
                    f"Unexpected error sending dispatch notification to {phone_number} for crisis {crisis.crisis_id}: {str(e)}",
                    exc_info=True
                )
                failed += 1
        
        logger.info(
            f"Dispatch notifications completed for crisis {crisis.crisis_id}: "
            f"{successful} successful, {failed} failed"
        )
        return (successful, failed)

