"""
场景 1 测试: 播放成龙喜剧片
预期: TV 播放, Light 调暗, Speaker 通知
"""
import pytest
from unittest.mock import MagicMock, patch
from client.brain import BrainClient
from core.types import DeviceInfo


@pytest.fixture
def brain_client():
    config = DeviceInfo(
        device_id="computer_001",
        name="Computer",
        role="computer",
        wisdom=90,
        output=True,
        skills=["screen_display", "execute_command"]
    )
    with patch('client.base.DiscoveryService'):
        with patch('client.base.TransportService'):
            with patch('client.base.ActorStateManager'):
                client = BrainClient(config)
                client.election.current_brain_id = "computer_001"
                return client


def test_scene1_intent_recognition(brain_client):
    """测试场景1: 意图识别"""
    intent = brain_client.llm.understand("放一部成龙的喜剧片")
    assert intent['intent'] == 'play_movie'
    assert 'actor' in intent['params']


def test_scene1_plan_generation(brain_client):
    """测试场景1: 计划生成"""
    intent = {'intent': 'play_movie', 'params': {'actor': '成龙', 'genre': '喜剧'}}
    plan = brain_client.llm.plan(intent, [])
    
    assert len(plan) >= 3  # play_video, set_light, speak_text
    
    tools = [step['tool'] for step in plan]
    assert 'play_video' in tools
    assert 'set_light' in tools
    assert 'speak_text' in tools
