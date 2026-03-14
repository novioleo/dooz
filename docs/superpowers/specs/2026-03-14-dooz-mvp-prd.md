# dooz MVP PRD

## 1. 项目概述

**项目名称**：dooz MVP - 分布式设备协作系统

**目标**：构建一个最小可行的去中心化设备协作系统，演示多设备自发现、脑选举、任务分发、多设备协作执行与结果通知能力。

**技术栈**：
- Python 3.10+
- FastDDS Python 绑定 (`fastdds`)
- Tailscale (VPN)
- OpenAI API (LLM for Brain)

---

## 2. 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        dooz MVP System                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    Python Client                          │   │
│  │                                                            │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐     │   │
│  │  │Computer │  │  Phone  │  │ Speaker │  │   TV    │     │   │
│  │  │ 90/✅   │  │  70/✅   │  │  50/✅   │  │  60/✅   │     │   │
│  │  │Output:Y │  │Output:Y │  │Output:Y │  │Output:Y │     │   │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘     │   │
│  │                                                            │   │
│  │  ┌─────────────────────────────────────────────────┐     │   │
│  │  │           Light (30/❌, Output:N)               │     │   │
│  │  │           ❌ Cannot be brain (wisdom < 50)      │     │   │
│  │  └─────────────────────────────────────────────────┘     │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│                    ┌─────────────────────┐                     │
│                    │   Brain (Computer)  │                     │
│                    │  ┌───────────────┐  │                     │
│                    │  │ LLM Agent     │  │                     │
│                    │  │ - Intent Parse│  │                     │
│                    │  │ - Tool Call   │  │                     │
│                    │  │ - Task Plan   │  │                     │
│                    │  └───────────────┘  │                     │
│                    │  ┌───────────────┐  │                     │
│                    │  │ Tool Registry │  │                     │
│                    │  │ - search_movie│  │                     │
│                    │  │ - play_video  │  │                     │
│                    │  │ - set_light   │  │                     │
│                    │  │ - speak_text  │  │                     │
│                    │  └───────────────┘  │                     │
│                    └─────────────────────┘                     │
│                                                                  │
│                      FastDDS Pub/Sub                            │
│                  (Over Tailscale VPN)                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. 大脑选举规则

### 3.1 选举条件

```
Brain Condition: 
  wisdom >= 50 AND is_online
```

### 3.2 设备角色

| 客户端 | Wisdom | 可当大脑 | Output | Skill |
|--------|--------|----------|--------|-------|
| computer | 90 | ✅ | ✅ | screen_display, execute_command |
| phone | 70 | ✅ | ✅ | send_notification, vibrate |
| tv | 60 | ✅ | ✅ | display_video, display_image |
| speaker | 50 | ✅ (刚好及格) | ✅ | play_audio, set_volume |
| light | 30 | ❌ | ❌ | toggle_light, set_brightness |

---

## 4. 场景设计

### 场景 1：播放成龙喜剧片

**触发**：用户在手机端输入 "放一部成龙的喜剧片"

**预期效果**：
1. Phone 收集请求 → 发送给 Brain (Computer)
2. Brain 通过 LLM 理解意图 → 搜索片源
3. Brain 调度多设备协作：
   - TV: 播放视频
   - Light: 调低亮度
   - Speaker: 通知用户 "《xxx》电影已经为您准备好"
4. 各设备更新 Actor States

### 场景 2：晚餐氛围

**触发**：用户在手机端输入 "我要吃晚饭了"

**预期效果**：
1. Phone 收集请求 → 发送给 Brain (Computer)
2. Brain 通过 LLM 理解意图 → 用户要吃晚饭，需要营造用餐氛围
3. Brain 调度多设备协作：
   - Light: 调暗到 30%
   - Speaker: 播放轻柔背景音乐
   - TV: 调暗到 50%
4. 各设备更新 Actor States

---

## 5. 功能需求

### 5.1 设备发现

- [x] Client 启动后通过 FastDDS 自动发现同域设备
- [x] 心跳保活（每 3 秒发送一次）
- [x] 设备离线检测（心跳超时 10 秒移除）
- [x] 打印当前在线设备列表

### 5.2 大脑选举

- [x] 启动时根据 wisdom 值确定大脑（wisdom >= 50）
- [x] 广播大脑变更
- [x] 规则：wisdom 最高的在线设备
- [x] 无大脑情况处理（所有在线设备 wisdom < 50）

### 5.3 任务执行

- [x] 任意 client 向大脑发送任务请求
- [x] 大脑根据 skill 匹配执行者
- [x] 执行者执行任务
- [x] 大脑选择有 output 能力的 client 通知用户
- [x] 执行者和通知者更新 Actor States

### 5.4 Actor States

```python
@dataclass
class ActorState:
    device_id: str
    history: List[str]
    current: Optional[str]
    next_ops: List[str]
```

---

## 6. 消息协议

| Topic | 方向 | 内容 |
|-------|------|------|
| `dooz/device/announce` | Client → All | 设备上线 |
| `dooz/device/heartbeat` | Client → All | 心跳 |
| `dooz/device/offline` | Client → All | 离线 |
| `dooz/brain/election` | All → All | 大脑变更 |
| `dooz/brain/status` | Brain → All | 广播大脑状态 |
| `dooz/task/request` | Client → Brain | 用户请求 |
| `dooz/task/dispatch` | Brain → Executor | 分发任务 |
| `dooz/task/response` | Executor → Brain | 执行结果 |
| `dooz/task/notify` | Brain → Output | 通知用户 |
| `dooz/actor/update` | All → All | Actor 状态同步 |

---

## 7. 文件结构

```
dooz/
├── core/
│   ├── __init__.py
│   ├── discovery.py        # 设备发现
│   ├── election.py         # 大脑选举（含 wisdom >= 50 逻辑）
│   ├── transport.py        # 消息传输
│   ├── actor_state.py      # Actor 状态机
│   └── types.py            # 消息类型
├── client/
│   ├── __init__.py
│   ├── base.py             # Client 基类
│   ├── brain.py            # Brain 扩展
│   ├── skill_executor.py   # Skill 执行
│   └── main.py             # 入口
├── brain/
│   ├── __init__.py
│   ├── llm_client.py       # LLM 调用
│   ├── intent_parser.py    # 意图解析
│   ├── tool_registry.py    # 工具注册
│   └── tools/              # 内置工具
│       ├── __init__.py
│       ├── search_movie.py # 搜索电影
│       ├── play_video.py   # 播放视频
│       ├── set_light.py    # 灯光控制
│       └── speak.py        # 语音通知
├── config/
│   ├── computer.yaml
│   ├── phone.yaml
│   ├── speaker.yaml
│   ├── tv.yaml
│   └── light.yaml
├── skills/
│   ├── __init__.py
│   ├── screen_display.py
│   ├── send_notification.py
│   ├── play_audio.py
│   ├── display_video.py
│   ├── toggle_light.py
│   └── set_brightness.py
├── scripts/
│   ├── run_mvp.sh
│   └── vpn/
│       └── start_vpn.sh
├── requirements.txt
└── README.md
```

---

## 8. 验收标准

| # | 场景 | 预期结果 |
|---|------|----------|
| 1 | 启动 5 个 client | Computer/Phone/TV/Speaker 在线上榜，Light 在线但无大脑资格 |
| 2 | 查看大脑状态 | Computer (wisdom=90) 为大脑 |
| 3 | 仅启动 Light | 无大脑，任务请求返回 "No brain available" |
| 4 | 场景1: Phone 发送 "放一部成龙的喜剧片" | TV 播放，Light 变暗，Speaker 说 "《xxx》已准备好" |
| 5 | 场景2: Phone 发送 "我要吃晚饭了" | Light 30%，Speaker 播放音乐，TV 50% |
| 6 | 查看 Actor States | 各设备 current/history 正确更新 |
| 7 | Computer 离线 | TV (wisdom=60) 成为新大脑 |
