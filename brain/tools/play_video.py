import logging

logger = logging.getLogger(__name__)

def play_video_tool(url: str, title: str = None) -> dict:
    """播放视频工具"""
    logger.info(f"[Tool] Playing video: {title} from {url}")
    return {'success': True, 'message': f'Playing: {title or url}'}
