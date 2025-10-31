import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from forms.models import Form

class AnalyticsConsumer(AsyncWebsocketConsumer):
    
    async def connect(self):
        self.form_slug = self.scope['url_route']['kwargs']['form_slug']
        self.form_group_name = f'form_report_{self.form_slug}'
        
        self.user = self.scope['user']
        
        if await self.can_access_report(self.user, self.form_slug):
            await self.channel_layer.group_add(
                self.form_group_name,
                self.channel_name
            )
            await self.accept()
        else:
            await self.close(code=403)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.form_group_name,
            self.channel_name
        )

    # --- Handlers ---

    async def report_update(self, event):
        message = event['message']
        
        await self.send(text_data=json.dumps({
            'type': 'report_update',
            'message': message
        }))

    # --- Helper Functions ---
    
    @database_sync_to_async
    def can_access_report(self, user, form_slug):
        if not user.is_authenticated:
            return False
        
        try:
            return Form.objects.filter(unique_slug=form_slug, user=user).exists()
        except Form.DoesNotExist:
            return False