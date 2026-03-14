import logging

logger = logging.getLogger(__name__)

def set_light_tool(level: int = 100, state: str = None) -> dict:
    """设置灯光工具"""
    if state:
        logger.info(f"[Tool] Light state: {state}")
        return {'success': True, 'message': f'Light: {state}'}
    logger.info(f"[Tool] Light brightness: {level}%")
    return {'success': True, 'message': f'Brightness: {level}%'}
