"""Tests for intent detection."""

import pytest
from dooz_cli.clarification.intent_detector import IntentDetector, IntentType


def test_detect_create():
    """Test detecting create intent."""
    detector = IntentDetector()
    intent = detector.detect("创建一个任务")
    
    assert intent.type == IntentType.CREATE
    assert intent.confidence > 0.5


def test_detect_delete():
    """Test detecting delete intent."""
    detector = IntentDetector()
    intent = detector.detect("删除用户")
    
    assert intent.type == IntentType.DELETE


def test_detect_update():
    """Test detecting update intent."""
    detector = IntentDetector()
    intent = detector.detect("修改设置")
    
    assert intent.type == IntentType.UPDATE


def test_detect_list():
    """Test detecting list items intent."""
    detector = IntentDetector()
    intent = detector.detect("列出所有文件")
    
    assert intent.type == IntentType.LIST_ITEMS


def test_detect_enable():
    """Test detecting enable intent."""
    detector = IntentDetector()
    intent = detector.detect("开启服务")
    
    assert intent.type == IntentType.ENABLE


def test_detect_disable():
    """Test detecting disable intent."""
    detector = IntentDetector()
    intent = detector.detect("关闭服务")
    
    assert intent.type == IntentType.DISABLE


def test_detect_get_info():
    """Test detecting get info intent."""
    detector = IntentDetector()
    intent = detector.detect("什么是人工智能")
    
    assert intent.type == IntentType.GET_INFO


def test_detect_set_value():
    """Test detecting set value intent."""
    detector = IntentDetector()
    intent = detector.detect("设置音量为50")
    
    assert intent.type == IntentType.SET_VALUE


def test_detect_send_message():
    """Test detecting send message intent."""
    detector = IntentDetector()
    intent = detector.detect("发送消息给张三")
    
    assert intent.type == IntentType.SEND_MESSAGE


def test_entity_extraction_target():
    """Test extracting target entity from input."""
    detector = IntentDetector()
    intent = detector.detect("删除用户")
    
    assert "target" in intent.entities
    assert intent.entities["target"] == "user"


def test_entity_extraction_with_name():
    """Test extracting name entity from input."""
    detector = IntentDetector()
    intent = detector.detect("创建任务叫做测试任务")
    
    assert intent.type == IntentType.CREATE
    assert "name" in intent.entities
    assert intent.entities["name"] == "测试任务"


def test_missing_target_triggers_clarification():
    """Test that missing target triggers clarification."""
    detector = IntentDetector()
    intent = detector.detect("创建")
    
    assert intent.type == IntentType.CREATE
    assert "target" in intent.missing_fields


def test_detect_unknown():
    """Test unknown input returns UNKNOWN."""
    detector = IntentDetector()
    intent = detector.detect("你好啊")
    
    assert intent.type == IntentType.UNKNOWN
