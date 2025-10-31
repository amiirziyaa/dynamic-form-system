import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from forms.models import Form
from forms.permissions import IsFormOwner

logger = logging.getLogger(__name__)

class AnalyticsConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time form analytics updates.
    
    Connects to: ws://host/ws/v1/forms/{form_slug}/reports/live/
    Requires authentication and form ownership.
    
    Sends real-time updates when:
    - New submissions are received
    - Views are tracked
    - Analytics data changes
    """
    
    async def connect(self):
        self.form_slug = self.scope['url_route']['kwargs']['form_slug']
        self.form_group_name = f'form_report_{self.form_slug}'
        self.user = self.scope['user']
        
        try:
            if await self.can_access_report(self.user, self.form_slug):
                await self.channel_layer.group_add(
                    self.form_group_name,
                    self.channel_name
                )
                await self.accept()
                
                # Send initial connection confirmation
                await self.send(text_data=json.dumps({
                    'type': 'connection_established',
                    'form_slug': self.form_slug,
                    'message': 'Connected to real-time analytics feed'
                }))
                logger.info(f"WebSocket connected for form: {self.form_slug}, user: {self.user.id}")
            else:
                logger.warning(f"WebSocket connection denied for form: {self.form_slug}, user: {self.user.id}")
                await self.close(code=403)
        except Exception as e:
            logger.error(f"WebSocket connection error: {str(e)}")
            await self.close(code=500)

    async def disconnect(self, close_code):
        try:
            await self.channel_layer.group_discard(
                self.form_group_name,
                self.channel_name
            )
            logger.info(f"WebSocket disconnected for form: {self.form_slug}, code: {close_code}")
        except Exception as e:
            logger.error(f"WebSocket disconnect error: {str(e)}")

    # --- Message Handlers ---

    async def receive(self, text_data):
        """Handle incoming messages from client"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'ping':
                # Respond to ping for connection health check
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': data.get('timestamp')
                }))
            elif message_type == 'subscribe':
                # Client can subscribe to specific events
                await self.send(text_data=json.dumps({
                    'type': 'subscribed',
                    'events': data.get('events', [])
                }))
            else:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': f'Unknown message type: {message_type}'
                }))
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
        except Exception as e:
            logger.error(f"Error processing WebSocket message: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Internal server error'
            }))

    async def report_update(self, event):
        """Handle report_update events from channel layer"""
        try:
            await self.send(text_data=json.dumps({
                'type': 'report_update',
                'data': event.get('data', {}),
                'message': event.get('message', ''),
                'timestamp': event.get('timestamp')
            }))
        except Exception as e:
            logger.error(f"Error sending report_update: {str(e)}")

    async def submission_update(self, event):
        """Handle new submission events"""
        try:
            await self.send(text_data=json.dumps({
                'type': 'submission_update',
                'data': event.get('data', {}),
                'timestamp': event.get('timestamp')
            }))
        except Exception as e:
            logger.error(f"Error sending submission_update: {str(e)}")

    async def view_update(self, event):
        """Handle new view events"""
        try:
            await self.send(text_data=json.dumps({
                'type': 'view_update',
                'data': event.get('data', {}),
                'timestamp': event.get('timestamp')
            }))
        except Exception as e:
            logger.error(f"Error sending view_update: {str(e)}")

    # --- Helper Functions ---
    
    @database_sync_to_async
    def can_access_report(self, user, form_slug):
        """Check if user has permission to access form analytics"""
        if not user.is_authenticated:
            return False
        
        try:
            form = Form.objects.get(unique_slug=form_slug)
            # Check if user owns the form
            return form.user == user
        except Form.DoesNotExist:
            return False
        except Exception as e:
            logger.error(f"Error checking form access: {str(e)}")
            return False