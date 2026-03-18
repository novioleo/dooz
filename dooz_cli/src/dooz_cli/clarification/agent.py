"""Main Clarification Agent implementation."""

import logging
from typing import Optional

from .state import ClarificationState, Intent, IntentType
from .intent_detector import IntentDetector
from .questions import QuestionGenerator

logger = logging.getLogger("dooz_cli.clarification")


class ClarificationAgent:
    """Multi-turn clarification agent for requirement gathering."""
    
    MAX_TURNS = 3
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.state = ClarificationState(session_id=session_id)
        self._intent_detector = IntentDetector()
        self._question_generator = QuestionGenerator()
        self._pending_question: Optional[str] = None
    
    def process_message(self, user_input: str) -> Optional[str]:
        """Process user message and return response."""
        self.state.add_turn("user", user_input)
        
        # Check if we reached max turns
        if self.state.turn_count >= self.MAX_TURNS:
            self.state.complete()
            return self._generate_force_complete_response()
        
        # If we have a pending question, process the answer
        if self._pending_question and self.state.intent:
            return self._process_answer(user_input)
        
        # Detect intent from new message
        intent = self._intent_detector.detect(user_input)
        self.state.set_intent(intent)
        
        # Check if intent was recognized
        if intent.type == IntentType.UNKNOWN:
            # Try to extract any info and proceed
            target = self._intent_detector.extract_target(user_input)
            name = self._intent_detector.extract_name(user_input)
            if target or name:
                intent.type = IntentType.EXECUTE_TASK
                if target:
                    intent.entities["target"] = target
                if name:
                    intent.entities["name"] = name
                intent.missing_fields = []
                self.state.set_intent(intent)
                confirmation = self._question_generator.generate_confirmation(
                    intent.type,
                    intent.entities,
                )
                self.state.add_turn("agent", confirmation)
                self.state.complete()
                return confirmation
        
        # Check if we need clarification
        if intent.missing_fields:
            # Ask the first missing question
            missing = intent.missing_fields[0]
            question = self._question_generator.generate_question(
                intent.type,
                missing,
            )
            self._pending_question = missing
            self.state.add_turn("agent", question)
            return question
        
        # Intent is complete, generate confirmation
        confirmation = self._question_generator.generate_confirmation(
            intent.type,
            intent.entities,
        )
        self.state.add_turn("agent", confirmation)
        self.state.complete()
        return confirmation
    
    def _process_answer(self, answer: str) -> str:
        """Process answer to a clarification question."""
        if not self.state.intent:
            return "出错了，请重新开始。"
        
        pending = self._pending_question
        
        # Extract entity based on what we're asking about
        if pending == "target":
            target = self._intent_detector.extract_target(answer)
            if not target:
                # Try to use the answer as target name
                target = answer.strip()
            if target:
                self.state.intent.entities["target"] = target
                
        elif pending == "name":
            name = self._intent_detector.extract_name(answer)
            if not name:
                name = answer.strip()
            if name:
                self.state.intent.entities["name"] = name
                
        elif pending == "value":
            self.state.intent.entities["value"] = answer.strip()
            
        elif pending == "recipient":
            self.state.intent.entities["recipient"] = answer.strip()
            
        elif pending == "scope":
            scope = self._intent_detector.extract_scope(answer)
            if scope:
                self.state.intent.entities["scope"] = scope
            elif "全部" in answer or "所有" in answer:
                self.state.intent.entities["scope"] = "all"
            elif "特定" in answer or "某个" in answer:
                self.state.intent.entities["scope"] = "specific"
        
        # Clear pending question
        self._pending_question = None
        
        # Check if more clarification needed
        if self.state.intent.missing_fields:
            missing = self.state.intent.missing_fields[0]
            question = self._question_generator.generate_question(
                self.state.intent.type,
                missing,
            )
            self._pending_question = missing
            self.state.add_turn("agent", question)
            return question
        
        # All fields collected, confirm
        confirmation = self._question_generator.generate_confirmation(
            self.state.intent.type,
            self.state.intent.entities,
        )
        self.state.add_turn("agent", confirmation)
        self.state.complete()
        return confirmation
    
    def _generate_force_complete_response(self) -> str:
        """Generate response when max turns reached."""
        if self.state.intent and self.state.intent.type != IntentType.UNKNOWN:
            return self._question_generator.generate_confirmation(
                self.state.intent.type,
                self.state.intent.entities,
            )
        return "好的，我将尝试处理您的请求。"
    
    def get_clarified_request(self) -> Optional[dict]:
        """Get the clarified request in daemon format."""
        if not self.state.is_complete or not self.state.intent:
            return None
        
        intent = self.state.intent
        
        # Build goal string from entities
        action = self._get_action_phrase(intent.type)
        target = intent.entities.get("target", "")
        name = intent.entities.get("name", "")
        value = intent.entities.get("value", "")
        scope = intent.entities.get("scope", "")
        
        parts = []
        if scope == "all":
            parts.append("全部")
        parts.append(action)
        if name:
            parts.append(f"「{name}」")
        if target:
            parts.append(target)
        if value:
            parts.append(f"为「{value}」")
        
        goal = "".join(parts) if parts else f"执行{intent.type.value}"
        
        return {
            "session_id": self.session_id,
            "clarified_goal": goal,
            "intent_type": intent.type.value,
            "entities": intent.entities,
            "confidence": intent.confidence,
        }
    
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
    
    def reset(self):
        """Reset clarification state."""
        self.state = ClarificationState(session_id=self.session_id)
        self._pending_question = None
