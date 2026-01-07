"""
WebSocket Service for Crisis Management System

Handles WebSocket updates for real-time crisis information broadcasting.
"""
import json
import logging
from typing import List, Dict

import channels.layers
from asgiref.sync import async_to_sync
from django.db.models import QuerySet

logger = logging.getLogger(__name__)


class WebSocketService:
    """
    Service for broadcasting crisis updates via WebSocket.
    
    Provides optimized methods for sending crisis data to connected clients
    through Django Channels.
    """
    
    GROUP_NAME = "crises"
    
    def __init__(self):
        """Initialize WebSocket service."""
        self.channel_layer = channels.layers.get_channel_layer()
    
    def serialize_crises(self, crises: QuerySet) -> List[Dict]:
        """
        Serialize crisis queryset to JSON-serializable format.
        
        Args:
            crises: QuerySet of Crisis instances
            
        Returns:
            List of serialized crisis dictionaries
        """
        from ..serializer import CrisisSerializer
        serializer = CrisisSerializer(crises, many=True)
        return list(serializer.data)
    
    def broadcast_crises_update(self, crises: QuerySet) -> bool:
        """
        Broadcast crisis updates to all connected WebSocket clients.
        
        Uses optimized queryset to avoid loading all crises into memory.
        Only serializes the data needed for transmission.
        
        Args:
            crises: QuerySet of Crisis instances to broadcast
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Optimize query: only fetch what's needed
            # Using select_related and prefetch_related would be ideal,
            # but ManyToMany fields require prefetch_related which is already
            # handled by the serializer
            
            # Serialize crises data
            crises_data = self.serialize_crises(crises)
            
            # Broadcast to WebSocket group
            async_to_sync(self.channel_layer.group_send)(
                self.GROUP_NAME,
                {
                    "type": "crises_update",
                    "payload": json.dumps(crises_data)
                }
            )
            
            logger.info(
                f"Broadcasted crisis update to {len(crises_data)} crises via WebSocket"
            )
            return True
            
        except Exception as e:
            logger.error(
                f"Failed to broadcast crisis update via WebSocket: {str(e)}",
                exc_info=True
            )
            return False

