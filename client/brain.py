import logging
from client.base import Client
from brain.llm_client import LLMClient
from brain.tool_registry import ToolRegistry
from brain.tools import search_movie_tool, play_video_tool, set_light_tool, speak_tool

logger = logging.getLogger(__name__)


class BrainClient(Client):
    """大脑客户端 - 具备 LLM 理解和任务规划能力"""
    
    def __init__(self, config, llm_api_key: str = None):
        super().__init__(config)
        self.llm = LLMClient(api_key=llm_api_key)
        self.tool_registry = ToolRegistry()
        self._register_tools()
        
    def _register_tools(self):
        """注册可用工具"""
        self.tool_registry.register('search_movie', search_movie_tool)
        self.tool_registry.register('play_video', play_video_tool)
        self.tool_registry.register('set_light', set_light_tool)
        self.tool_registry.register('speak_text', speak_tool)
        
    def on_task_request(self, message: dict):
        """处理任务请求 (大脑专属)"""
        if not self.election.is_brain(self.device_id):
            logger.warning("Not brain, ignoring task request")
            return
            
        user_input = message.get('text', '')
        request_id = message.get('request_id', '')
        requester_id = message.get('requester_id', '')
        
        logger.info(f"[Brain] Processing request: {user_input}")
        
        # 1. 理解意图
        intent = self.llm.understand(user_input)
        
        # 2. 生成计划
        plan = self.llm.plan(intent, self.tool_registry.list_tools())
        
        # 3. 执行计划
        results = []
        for step in plan:
            tool_name = step.get('tool')
            params = step.get('params', {})
            
            result = self.tool_registry.execute(tool_name, **params)
            results.append({'tool': tool_name, 'result': result})
            
            # 调度到对应设备执行
            self._dispatch_to_device(tool_name, params, request_id)
            
        # 4. 通知用户
        self._notify_user(results, request_id)
        
    def _dispatch_to_device(self, tool_name: str, params: dict, request_id: str):
        """调度任务到对应设备"""
        # 根据 skill 名称找到执行者
        executor_id = self._find_executor(tool_name)
        
        if executor_id:
            import time
            dispatch_msg = {
                'msg_type': 'task/dispatch',
                'request_id': request_id,
                'skill_name': self._tool_to_skill(tool_name),
                'parameters': params,
                'executor_id': executor_id,
                'timestamp': time.time()
            }
            self.transport.publish('dooz/task/dispatch', dispatch_msg)
            logger.info(f"[Brain] Dispatched {tool_name} to {executor_id}")
            
    def _find_executor(self, tool_name: str) -> str:
        """找到能执行工具的设备"""
        skill_name = self._tool_to_skill(tool_name)
        
        # 获取在线设备
        devices = self.discovery.get_online_devices()
        devices[self.device_id] = self.config
        
        # 查找有对应 skill 的设备
        for device_id, device in devices.items():
            if skill_name in device.skills:
                return device_id
                
        return None
        
    def _tool_to_skill(self, tool_name: str) -> str:
        """工具名转 skill 名"""
        mapping = {
            'play_video': 'display_video',
            'set_light': 'set_brightness',
            'speak_text': 'play_audio',
            'play_audio': 'play_audio',
            'set_light_tv': 'set_brightness',
        }
        return mapping.get(tool_name, tool_name)
        
    def _notify_user(self, results: list, request_id: str):
        """通知用户结果"""
        import time
        
        # 找到有 output 能力的设备
        devices = self.discovery.get_online_devices()
        devices[self.device_id] = self.config
        
        output_devices = [d for d in devices.values() if d.output]
        
        if not output_devices:
            logger.warning("No output device available")
            return
            
        # 选择一个 output 设备 (简化: 选第一个)
        notify_device = output_devices[0].device_id
        
        # 构建通知消息
        notify_msg = {
            'msg_type': 'task/notify',
            'request_id': request_id,
            'message': '任务已完成',
            'source_id': self.device_id,
            'timestamp': time.time()
        }
        
        self.transport.publish('dooz/task/notify', notify_msg)
        logger.info(f"[Brain] Notified user via {notify_device}")
