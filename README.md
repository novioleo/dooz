# dooz

**分布式多智能体协作系统**

> 让每个设备成为真正的智能体，通过自然语言与用户交互，自主协作完成复杂任务。

[![Python](https://img.shields.io/badge/Python-3.10+-blue)](https://www.python.org/)
[![Status](https://img.shields.io/badge/Status-MVP-orange)]()

---

## 愿景

dooz 是一个分布式多智能体协作系统：

- **每个设备都是智能体**：手机、电视、音箱、灯都作为 Agent 接入
- **原生智能体协调**：每个租户有一个原生智能体（Native Agent）负责任务拆解和调度
- **LLM 能力共享**：租户配置一次 LLM，所有智能体都能调用
- **设备间直接协作**：通过 Pub/Sub 消息机制，智能体之间可以直接协作

---

## 架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           dooz 云端服务器                               │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                      API Server (FastAPI)                      │   │
│  │  - OAuth2 认证                                                  │   │
│  │  - 租户管理                                                    │   │
│  │  - LLM 代理 (租户配置自己的 LLM Provider)                     │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │              FastDDS Gateway (per tenant)                       │   │
│  │  - Topic: dooz/{tenant_id}/...                                │   │
│  │  - WebSocket ↔ FastDDS 桥接                                   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                    ▲
                                    │
                              WebSocket
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    dooz Client (多语言)                                │
│                                                                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐       │
│  │   Python        │  │   Kotlin        │  │   Swift         │       │
│  │   (MVP)         │  │   (Future)      │  │   (Future)      │       │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘       │
└─────────────────────────────────────────────────────────────────────────┘
```

### 核心概念

| 概念 | 说明 |
|------|------|
| **租户 (Tenant)** | 独立的逻辑单元，有自己的 LLM 配置和设备列表 |
| **原生智能体 (Native Agent)** | 每个租户的主要协调者，负责任务拆解和调度 |
| **设备智能体** | 接入的终端设备，具备不同能力和技能 |
| **LLM 代理** | Server 代理 LLM 请求，组装 Profile + Memory + Soul 作为 Context |

### 消息流程

```
用户 (任意设备)
    │
    ▼
Pub: task/request (到租户的 Topic)
    │
    ▼
Native Agent (收到请求)
    │
    ├── 调用 LLM 分析任务
    │
    ▼
Pub: task/dispatch (分发子任务到各设备)
    │
    ▼
各设备执行 skill → 返回 task/response
    │
    ▼
Native Agent 汇总 → Pub: task/notify (通知用户)
```

---

## MVP 范围

当前 MVP 聚焦于最小可用功能：

### 已实现 (Phase 1)

- [ ] Server 基础结构 (FastAPI)
- [ ] OAuth2 认证
- [ ] 租户管理 (创建、配置 LLM Provider)
- [ ] FastDDS Gateway (MVP: 内存模式)
- [ ] WebSocket 连接
- [ ] LLM 代理接口
- [ ] Python Client 基础
- [ ] 设备 skills (开灯、播放视频等)

### 待实现 (Future)

- [ ] Chat Session 管理 + Memory 总结
- [ ] Profile / Soul / Memory 完整 API
- [ ] 任务超时重派机制
- [ ] 设备间复杂协作
- [ ] Kotlin / Swift Client
- [ ] 真实 FastDDS 集成
- [ ] 持久化存储

---

## 快速开始

### 1. 启动 Server

```bash
cd dooz
pip install -r requirements.txt
python -m server.main
```

Server 会在 `http://localhost:8000` 启动。

### 2. 创建租户

```bash
curl -X POST http://localhost:8000/tenant/create \
  -H "Content-Type: application/json" \
  -d '{
    "name": "我的家庭",
    "llm_url": "https://api.openai.com/v1/chat/completions",
    "llm_api_key": "sk-xxx",
    "llm_model": "gpt-4"
  }'
```

返回:
```json
{
  "tenant_id": "tenant-xxx",
  "name": "我的家庭",
  ...
}
```

### 3. 启动 Client

编辑 `client/python/config/devices/computer.yaml`:

```yaml
device:
  id: "computer-001"
  name: "客厅电脑"
  wisdom: 90
  output: true
  llm_enabled: true
  skills:
    - name: "display_video"
    - name: "screen_display"

server:
  url: "http://localhost:8000"
  tenant_id: "tenant-xxx"
  auth:
    client_id: "xxx"
    client_secret: "xxx"
```

运行:
```bash
python -m client.python.main --config config/devices/computer.yaml
```

---

## 文件结构

```
dooz/
├── server/                    # 服务器端
│   ├── main.py               # FastAPI 入口
│   ├── api/                  # API 路由
│   ├── core/                 # 核心类型
│   ├── tenant/               # 租户管理
│   ├── llm/                  # LLM 网关
│   └── transport/            # FastDDS Gateway
│
├── client/                   # 客户端
│   ├── python/              # Python Client (MVP)
│   │   ├── core/           # 核心模块
│   │   ├── skills/         # 设备技能
│   │   └── config/         # 配置文件
│   ├── kotlin/              # Kotlin Client (Future)
│   └── swift/              # Swift Client (Future)
│
└── docs/                    # 文档
    └── superpowers/
        └── specs/          # 设计文档
```

---

## 文档

| 文档 | 说明 |
|------|------|
| [设计文档](docs/superpowers/specs/2026-03-14-dooz-architecture-design.md) | 完整架构设计 |
| [实现计划](docs/superpowers/plans/2026-03-14-dooz-mvp-implementation-plan.md) | MVP 实现计划 |

---

## 技术栈

| 组件 | 技术 |
|------|------|
| Server | FastAPI, Python 3.10+ |
| Transport | FastDDS (MVP: 内存模式) |
| Auth | OAuth2 (JWT) |
| Client | Python (MVP), Kotlin/Swift (Future) |

---

## License

Apache License 2.0 - see [LICENSE](LICENSE)
