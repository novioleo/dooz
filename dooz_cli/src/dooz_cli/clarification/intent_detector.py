"""Intent detection for clarification agent."""

import re
from typing import Optional

from .state import Intent, IntentType


class IntentDetector:
    """Detects user intent from natural language input."""
    
    # Generic intent patterns - applicable to various domains
    INTENT_PATTERNS: dict[IntentType, list[str]] = {
        # Information retrieval
        IntentType.GET_INFO: [
            r"什么是",
            r"告诉我.*",
            r"查询",
            r"查找",
            r"搜索",
            r"了解",
            r"查看",
        ],
        IntentType.LIST_ITEMS: [
            r"列出",
            r"列表",
            r"显示.*列表",
            r"有哪些",
            r"有什么",
        ],
        
        # Action execution
        IntentType.CREATE: [
            r"创建",
            r"新建",
            r"添加",
            r"增加",
        ],
        IntentType.UPDATE: [
            r"更新",
            r"修改",
            r"编辑",
            r"改变",
            r"调整",
        ],
        IntentType.DELETE: [
            r"删除",
            r"移除",
            r"去掉",
        ],
        
        # Task execution
        IntentType.EXECUTE_TASK: [
            r"执行",
            r"运行",
            r"开始",
            r"完成",
            r"做.*",
        ],
        IntentType.STOP_TASK: [
            r"停止",
            r"暂停",
            r"终止",
        ],
        
        # Status/control
        IntentType.ENABLE: [
            r"开启",
            r"启动",
            r"打开",
            r"启用",
            r"激活",
        ],
        IntentType.DISABLE: [
            r"关闭",
            r"停用",
            r"禁用",
            r"关掉",
        ],
        
        # Settings
        IntentType.SET_VALUE: [
            r"设置",
            r"设定",
            r"调整.*为",
            r"改成",
        ],
        IntentType.GET_STATUS: [
            r"状态",
            r"情况",
            r"如何",
            r"怎么样",
        ],
        
        # Communication
        IntentType.SEND_MESSAGE: [
            r"发送.*给",
            r"通知",
            r"告诉.*说",
            r"发.*消息",
        ],
        IntentType.READ_MESSAGE: [
            r"读取.*消息",
            r"查看.*消息",
            r"未读",
        ],
        
        # File operations
        IntentType.DOWNLOAD: [
            r"下载",
            r"获取.*文件",
        ],
        IntentType.UPLOAD: [
            r"上传",
        ],
        
        # Generic help
        IntentType.HELP: [
            r"帮助",
            r"帮忙",
            r"怎么.*做",
            r"如何.*",
        ],
        
        # Fallback unknown
        IntentType.UNKNOWN: [],
    }
    
    # Generic entity patterns
    TARGET_PATTERNS = {
        "file": [r".*\.(pdf|doc|docx|txt|jpg|png|mp3|mp4)", r"文件"],
        "user": [r"用户", r"用户.*", r"@.*"],
        "task": [r"任务", r"作业"],
        "setting": [r"设置", r"配置", r"选项"],
        "message": [r"消息", r"通知", r"邮件"],
        "schedule": [r"日程", r"预约", r"会议"],
    }
    
    SCOPE_PATTERNS = {
        "all": [r"全部", r"所有", r"所有.*"],
        "current": [r"当前", r"这个", r"现在的"],
        "specific": [r"指定", r"特定", r"某个"],
    }
    
    def detect(self, text: str) -> Intent:
        """Detect intent from user input."""
        text = text.strip().lower()
        
        # Try to match intent patterns
        for intent_type, patterns in self.INTENT_PATTERNS.items():
            if intent_type == IntentType.UNKNOWN:
                continue
            for pattern in patterns:
                if re.search(pattern, text):
                    return self._build_intent(intent_type, text)
        
        # No match found - return unknown
        return Intent(
            type=IntentType.UNKNOWN,
            confidence=0.0,
        )
    
    def _build_intent(self, intent_type: IntentType, text: str) -> Intent:
        """Build intent with entity extraction."""
        entities = {}
        missing_fields = []
        
        # Extract target (what the action is on)
        target = self._extract_entity(text, self.TARGET_PATTERNS)
        if target:
            entities["target"] = target
        else:
            # Most intents need a target
            missing_fields.append("target")
        
        # Extract scope
        scope = self._extract_entity(text, self.SCOPE_PATTERNS)
        if scope:
            entities["scope"] = scope
        
        # Extract specific identifier (name, id, etc.)
        id_match = re.search(r"(?:叫做|名为|叫|id[:\s]*)([^\s，。,]+)", text)
        if id_match:
            entities["name"] = id_match.group(1)
        
        return Intent(
            type=intent_type,
            confidence=0.8,
            entities=entities,
            missing_fields=missing_fields,
        )
    
    def _extract_entity(self, text: str, patterns: dict) -> Optional[str]:
        """Extract entity from text using patterns."""
        for entity_type, regex_patterns in patterns.items():
            for pattern in regex_patterns:
                if re.search(pattern, text):
                    return entity_type
        return None
    
    def extract_target(self, text: str) -> Optional[str]:
        """Public method to extract target entity."""
        return self._extract_entity(text, self.TARGET_PATTERNS)
    
    def extract_name(self, text: str) -> Optional[str]:
        """Extract name/identifier from text."""
        id_match = re.search(r"(?:叫做|名为|叫|id[:\s]*|名称[:\s]*)([^\s，。,]+)", text)
        if id_match:
            return id_match.group(1)
        return None
    
    def extract_scope(self, text: str) -> Optional[str]:
        """Public method to extract scope."""
        return self._extract_entity(text, self.SCOPE_PATTERNS)
