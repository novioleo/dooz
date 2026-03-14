import logging

logger = logging.getLogger(__name__)

def speak_tool(message: str) -> dict:
    """语音通知工具"""
    logger.info(f"[Tool] Speaking: {message}")
    return {'success': True, 'message': f'Speaking: {message}'}
