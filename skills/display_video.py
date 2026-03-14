import logging

logger = logging.getLogger(__name__)

class DisplayVideoSkill:
    name = "display_video"
    
    def execute(self, **params) -> dict:
        url = params.get('url', '')
        title = params.get('title', 'Video')
        logger.info(f"[DisplayVideo] Playing: {title} from {url}")
        return {'success': True, 'message': f'Playing: {title}'}
