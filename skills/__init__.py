"""Skill 定义模块"""

from .screen_display import ScreenDisplaySkill
from .send_notification import SendNotificationSkill
from .play_audio import PlayAudioSkill
from .display_video import DisplayVideoSkill
from .toggle_light import ToggleLightSkill
from .set_brightness import SetBrightnessSkill

SKILL_REGISTRY = {
    'screen_display': ScreenDisplaySkill(),
    'send_notification': SendNotificationSkill(),
    'play_audio': PlayAudioSkill(),
    'display_video': DisplayVideoSkill(),
    'toggle_light': ToggleLightSkill(),
    'set_brightness': SetBrightnessSkill(),
}

def get_skill(skill_name: str):
    """获取 skill 实例"""
    return SKILL_REGISTRY.get(skill_name)
