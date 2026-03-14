"""
场景 2 测试: 晚餐氛围
预期: Light 30%, Speaker 播放音乐, TV 50%
"""
import pytest
from client.brain import BrainClient
from core.types import DeviceInfo
from unittest.mock import patch


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


def test_scene2_intent_recognition(brain_client):
    """测试场景2: 意图识别"""
    intent = brain_client.llm.understand("我要吃晚饭了")
    assert intent['intent'] == 'dinner_mode'


def test_scene2_plan_generation(brain_client):
    """测试场景2: 计划生成"""
    intent = {'intent': 'dinner_mode', 'params': {}}
    plan = brain_client.llm.plan(intent, [])
    
    assert len(plan) >= 2  # set_light, play_audio, set_light_tv
    
    tools = [step['tool'] for step in plan]
    assert 'set_light' in tools
    assert 'play_audio' in tools
