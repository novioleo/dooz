import logging

logger = logging.getLogger(__name__)

class ScreenDisplaySkill:
    name = "screen_display"
    
    def execute(self, **params) -> dict:
        message = params.get('message', '')
        logger.info(f"[ScreenDisplay] Displaying: {message}")
        return {'success': True, 'message': f'Screen: {message}'}
