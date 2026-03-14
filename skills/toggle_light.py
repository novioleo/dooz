import logging

logger = logging.getLogger(__name__)

class ToggleLightSkill:
    name = "toggle_light"
    
    def execute(self, **params) -> dict:
        state = params.get('state', 'toggle')
        logger.info(f"[ToggleLight] Light turned {state}")
        return {'success': True, 'message': f'Light: {state}'}
