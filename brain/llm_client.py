"""
LLM 客户端 (MVP: 简化版)
生产环境应使用真实 OpenAI API
"""
import logging

logger = logging.getLogger(__name__)


class LLMClient:
    """LLM 客户端 - 理解用户意图并生成执行计划"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        
    def understand(self, user_input: str) -> dict:
        """理解用户输入"""
        logger.info(f"[LLM] Understanding: {user_input}")
        
        # MVP: 简化实现，基于规则匹配
        if "电影" in user_input or "喜剧片" in user_input:
            if "成龙" in user_input:
                return {
                    'intent': 'play_movie',
                    'params': {'actor': '成龙', 'genre': '喜剧'}
                }
            return {'intent': 'play_movie', 'params': {}}
            
        if "晚饭" in user_input or "吃饭" in user_input or "晚餐" in user_input:
            return {'intent': 'dinner_mode', 'params': {}}
            
        return {'intent': 'unknown', 'params': {}}
        
    def plan(self, intent: dict, available_tools: list) -> list:
        """生成执行计划"""
        logger.info(f"[LLM] Planning for intent: {intent}")
        
        if intent['intent'] == 'play_movie':
            # 1. 先搜索电影
            movie = self._call_tool('search_movie', **intent['params'])
            
            # 2. 然后播放、调光、通知
            plan = [
                {'tool': 'play_video', 'params': {'url': movie.get('url'), 'title': movie.get('title')}},
                {'tool': 'set_light', 'params': {'level': 30}},
                {'tool': 'speak_text', 'params': {'message': f'《{movie.get("title", "电影")}》已经为您准备好'}}
            ]
            
        elif intent['intent'] == 'dinner_mode':
            plan = [
                {'tool': 'set_light', 'params': {'level': 30}},
                {'tool': 'play_audio', 'params': {'type': 'background_music', 'message': '轻柔背景音乐'}},
                {'tool': 'set_light_tv', 'params': {'level': 50}}
            ]
            
        else:
            plan = []
            
        return plan
        
    def _call_tool(self, tool_name: str, **kwargs) -> dict:
        """调用工具"""
        # MVP: 简化实现
        if tool_name == 'search_movie':
            actor = kwargs.get('actor', '')
            if "成龙" in actor:
                return {'title': '功夫瑜伽', 'url': 'https://example.com/kung_fu_yoga.mp4'}
            return {'title': '电影', 'url': 'https://example.com/movie.mp4'}
        return {}
