"""Daemon configuration."""

from pathlib import Path

from pydantic import BaseModel, Field


class MqttConfig(BaseModel):
    """MQTT broker configuration."""
    broker: str = Field(default="localhost", description="MQTT broker host")
    port: int = Field(default=1883, description="MQTT broker port")
    client_id: str = Field(default="daemon", description="MQTT client ID")


class MonitorConfig(BaseModel):
    """Monitor agent configuration."""
    heartbeat_interval: int = Field(default=10, description="Heartbeat interval in seconds")
    offline_threshold: int = Field(default=30, description="Offline threshold in seconds")


class DaemonConfig(BaseModel):
    """Daemon server configuration."""
    host: str = Field(default="0.0.0.0", description="WebSocket server host")
    port: int = Field(default=8765, description="WebSocket server port")
    mqtt: MqttConfig = Field(default_factory=MqttConfig)
    monitor: MonitorConfig = Field(default_factory=MonitorConfig)
    definitions_dir: Path = Field(
        default=Path("./definitions"),
        description="Directory containing dooz and agent definitions"
    )


def load_config(**kwargs) -> DaemonConfig:
    """Load daemon configuration from kwargs."""
    return DaemonConfig(**kwargs)
