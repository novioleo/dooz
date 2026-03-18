"""Clarification question generation."""

from typing import Optional

from .state import IntentType


class QuestionGenerator:
    """Generates clarifying questions based on missing information."""
    
    # Generic questions mapped by (intent_type, missing_field)
    QUESTIONS: dict[tuple[IntentType, str], str] = {
        # Missing target (what to act on)
        (IntentType.GET_INFO, "target"): "请问您想了解什么信息？",
        (IntentType.CREATE, "target"): "请问您想创建什么？",
        (IntentType.UPDATE, "target"): "请问您想修改什么？",
        (IntentType.DELETE, "target"): "请问您想删除什么？",
        (IntentType.EXECUTE_TASK, "target"): "请问您想执行什么任务？",
        (IntentType.ENABLE, "target"): "请问您想启用什么？",
        (IntentType.DISABLE, "target"): "请问您想禁用什么？",
        (IntentType.SET_VALUE, "target"): "请问您想设置什么？",
        (IntentType.DOWNLOAD, "target"): "请问您想下载什么？",
        (IntentType.UPLOAD, "target"): "请问您想上传什么？",
        (IntentType.SEND_MESSAGE, "target"): "请问您想发送什么内容？",
        
        # Missing name/identifier
        (IntentType.CREATE, "name"): "请问它的名称是什么？",
        (IntentType.UPDATE, "name"): "请问您想修改的是哪个？",
        (IntentType.DELETE, "name"): "请问您想删除的是哪个？",
        
        # Missing value (for set operations)
        (IntentType.SET_VALUE, "value"): "请问您想设置为什么值？",
        
        # Missing recipient (for send operations)
        (IntentType.SEND_MESSAGE, "recipient"): "请问您想发送给谁？",
        
        # Missing scope
        (IntentType.LIST_ITEMS, "scope"): "请问您想列出全部还是特定的？",
        (IntentType.DELETE, "scope"): "请问是删除单个还是全部？",
    }
    
    DEFAULT_QUESTIONS: dict[str, str] = {
        "target": "请问您具体想做什么？",
        "name": "请问名称或标识是什么？",
        "value": "请问具体值是什么？",
        "recipient": "请问是给谁的？",
        "scope": "请问是特定还是全部？",
    }
    
    def generate_question(
        self,
        intent_type: IntentType,
        missing_field: Optional[str],
    ) -> Optional[str]:
        """Generate a clarification question."""
        if missing_field is None:
            return None
        
        # Try specific question first
        key = (intent_type, missing_field)
        if key in self.QUESTIONS:
            return self.QUESTIONS[key]
        
        # Fall back to default
        if missing_field in self.DEFAULT_QUESTIONS:
            return self.DEFAULT_QUESTIONS[missing_field]
        
        return None
    
    def generate_confirmation(self, intent_type: IntentType, entities: dict[str, str]) -> str:
        """Generate a confirmation message based on intent and entities."""
        target = entities.get("target", "")
        name = entities.get("name", "")
        value = entities.get("value", "")
        scope = entities.get("scope", "")
        recipient = entities.get("recipient", "")
        
        # Build action phrase
        action = self._get_action_phrase(intent_type)
        
        # Build target phrase
        target_phrase = ""
        if name:
            target_phrase = f"「{name}」"
        elif target:
            target_phrase = f"「{target}」"
        
        # Build value phrase
        value_phrase = f"为「{value}」" if value else ""
        
        # Build scope phrase
        scope_phrase = ""
        if scope == "all":
            scope_phrase = "全部"
        elif scope == "specific":
            scope_phrase = "特定的"
        
        # Build full confirmation
        parts = []
        if scope_phrase:
            parts.append(scope_phrase)
        parts.append(action)
        if target_phrase:
            parts.append(target_phrase)
        if value_phrase:
            parts.append(value_phrase)
        if recipient:
            parts.append(f"给{recipient}")
        
        result = "".join(parts)
        
        # Add punctuation
        if result:
            return result + "，对吗？"
        
        return "好的，我来处理这个请求，对吗？"
    
    def _get_action_phrase(self, intent_type: IntentType) -> str:
        """Get action phrase for intent type."""
        phrases = {
            IntentType.GET_INFO: "了解",
            IntentType.LIST_ITEMS: "列出",
            IntentType.GET_STATUS: "查看",
            IntentType.CREATE: "创建",
            IntentType.UPDATE: "修改",
            IntentType.DELETE: "删除",
            IntentType.EXECUTE_TASK: "执行",
            IntentType.STOP_TASK: "停止",
            IntentType.ENABLE: "启用",
            IntentType.DISABLE: "禁用",
            IntentType.SET_VALUE: "设置",
            IntentType.SEND_MESSAGE: "发送",
            IntentType.READ_MESSAGE: "读取",
            IntentType.DOWNLOAD: "下载",
            IntentType.UPLOAD: "上传",
            IntentType.HELP: "帮助",
            IntentType.UNKNOWN: "处理",
        }
        return phrases.get(intent_type, "处理")
