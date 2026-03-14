"""Skills - 设备技能."""

from typing import Optional


class Skill:
    """Skill 基类."""
    
    def execute(self, **kwargs) -> dict:
        """执行 skill."""
        raise NotImplementedError


class LightSkill(Skill):
    """灯光控制技能."""
    
    def execute(self, action: str = "toggle", **kwargs):
        print(f"[Light] Action: {action}, kwargs: {kwargs}")
        return {"success": True, "message": f"Light {action} done"}


class DisplayVideoSkill(Skill):
    """视频播放技能."""
    
    def execute(self, video: str = "", **kwargs):
        print(f"[DisplayVideo] Playing: {video}")
        return {"success": True, "message": f"Playing {video}"}


class AudioSkill(Skill):
    """音频播放技能."""
    
    def execute(self, audio: str = "", **kwargs):
        print(f"[Audio] Playing: {audio}")
        return {"success": True, "message": f"Playing audio: {audio}"}


class NotificationSkill(Skill):
    """通知技能."""
    
    def execute(self, message: str = "", **kwargs):
        print(f"[Notification] {message}")
        return {"success": True, "message": f"Notified: {message}"}


class ScreenDisplaySkill(Skill):
    """屏幕显示技能."""
    
    def execute(self, content: str = "", **kwargs):
        print(f"[Screen] Displaying: {content}")
        return {"success": True, "message": f"Displayed: {content}"}


# Skill 注册表
SKILLS = {
    "toggle_light": LightSkill(),
    "set_brightness": LightSkill(),
    "display_video": DisplayVideoSkill(),
    "play_audio": AudioSkill(),
    "send_notification": NotificationSkill(),
    "screen_display": ScreenDisplaySkill(),
}


def get_skill(name: str) -> Optional[Skill]:
    """获取 skill 实例."""
    return SKILLS.get(name)


__all__ = ["Skill", "get_skill", "SKILLS"]
