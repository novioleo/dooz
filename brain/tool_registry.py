import logging
from typing import Dict, Any, Callable

logger = logging.getLogger(__name__)


class ToolRegistry:
    """工具注册表 - 管理大脑可用的工具"""
    
    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        
    def register(self, name: str, tool: Callable):
        """注册工具"""
        self._tools[name] = tool
        logger.info(f"Tool registered: {name}")
        
    def execute(self, tool_name: str, **kwargs) -> Any:
        """执行工具"""
        if tool_name not in self._tools:
            logger.error(f"Tool not found: {tool_name}")
            return {'success': False, 'error': f'Tool {tool_name} not found'}
            
        try:
            result = self._tools[tool_name](**kwargs)
            logger.info(f"Tool executed: {tool_name} -> {result}")
            return result
        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            return {'success': False, 'error': str(e)}
            
    def list_tools(self) -> list:
        """列出所有工具"""
        return list(self._tools.keys())
