# 分布式Agents管理平台 架构设计文档

| 文档版本 | 修改日期 | 修改内容 | 作者 |
| :--- | :--- | :--- | :--- |
| v1.0 | 2026-07-10 | 初稿创建 | - |

---

## 1. 背景与目标

### 1.1 项目背景

随着AI Agent技术的快速发展，企业需要在一个统一的平台上**部署、管理和调度**大量的AI Agent实例（如OpenCode、AutoGPT、CrewAI等）。这些Agent实例需要分布在多台物理机或虚拟机上，形成一个可水平扩展的分布式Agent集群。

### 1.2 项目目标

构建一个**轻量级、可扩展、易运维**的分布式Agents管理平台，对标OpenStack Nova的计算资源管理能力，但专为AI Agent场景优化。

### 1.3 设计原则

| 原则 | 说明 |
| :--- | :--- |
| **KISS原则** | 第一版保持简单，全HTTP通信，不引入消息队列 |
| **模块化** | Master、Scheduler、Node三个服务职责清晰，可独立部署 |
| **无状态优先** | Master和Scheduler无状态，便于水平扩展 |
| **自愈能力** | Agent异常退出时Node自动重启，Node离线时Master自动摘除 |
| **兼容性** | 支持多种Agent运行时（例如：OpenCode） |

---

## 2. 总体架构

### 2.1 架构概览

```
                        ┌─────────────────┐
                        │ 客户端/用户     │
                        └────────┬────────┘
                                 │ HTTPS
                                 ▼
┌────────────────────────────────────────────────────────────┐
│ Master (控制节点)                                          │
│ ┌──────────────┐ ┌───────────────┐ ┌─────────────────────┐ │
│ │ API Gateway  │ │  ...          │ │ ...                 │ │
│ │ (路由/鉴权)  │ │ (待定)      │ │ (待定)              │ │
│ └──────────────┘ └───────────────┘ └─────────────────────┘ │
└─────────────────────────────┬──────────────────────────────┘
                              │ HTTP (管理平面)
              ┌───────────────┴───────────────┐
              ▼                               ▼
    ┌─────────────────────────┐ ┌─────────────────────────┐
    │ Scheduler (调度器)      │ │ Node (执行节点)         │
    │ ┌─────────────────────┐ │ │ ┌─────────────────────┐ │
    │ │ 资源评估与选主引擎  │ │ │ │ Agent生命周期管理器 │ │
    │ │ 调度策略插件化      │ │ │ │ 进程/容器启动器     │ │
    │ └─────────────────────┘ │ │ │ 资源监控与上报      │ │
    │                         │ │ │ 日志收集与存储      │ │
    │ 可独立扩展，无状态      │ │ └─────────────────────┘ │
    └─────────────────────────┘ └───────────┬─────────────┘
                                            │ 管理
                                            ▼
                                ┌─────────────────────────┐
                                │ Agent实例集群           │
                                │ ┌─────┐ ┌─────┐ ┌─────┐ │
                                │ │Agent│ │Agent│ │Agent│ │
                                │ │   A │ │ B   │ │ C   │ │
                                │ └─────┘ └─────┘ └─────┘ │
                                │ (OpenCode / 其他Agent)  │
                                └─────────────────────────┘
```


### 2.2 服务职责矩阵

| 服务 | 核心职责 | 是否状态 | 扩展方式 | 端口建议 |
| :--- | :--- | :--- | :--- | :--- |
| **Master** | 统一入口、Agent注册、请求路由 | 无状态 | 水平扩展（前置LB） | 8080 |
| **Scheduler** | 资源评估、Agent择优选主 | 无状态 | 水平扩展 | 8081 |
| **Node** | Agent生命周期管理、资源监控 | 有状态 | 水平扩展（每台物理机一个） | 8082 |

---

## 3. 服务详细设计

### 3.1 Master 服务

#### 3.1.1 职责定义

Master是整个平台的**大脑和门户**，负责接收所有外部请求，维护全局Agent注册表，并将任务路由到合适的Node。

#### 3.1.2 核心模块

| 模块 | 功能描述 |
| :--- | :--- |
| **API Gateway** | 提供RESTful API，处理认证鉴权（JWT）、请求限流、访问日志 |
3.1.4 主要命令行

- agentstack service list
- agentstack user list
- agentstack project list
- agentstack agent list
- agentstack agent create
- agentstack agent delete

3.1.4 主要API

| 方法 | 路径 | 功能 |
| :--- | :--- | :--- |
| GET   | /api/v1/agents            | 列出所有Agent         | 
| POST	| /api/v1/agents	        | 创建Agent实例         | 
| DELETE| /api/v1/agents/{id}	    | 删除Agent实例         | 
| GET	| /api/v1/agents/{id}       | 查询Agent详情         |
| POST  | /api/v1/agents/{id}/start | 启动已停止的Agent     | 
| POST  | /api/v1/agents/{id}/stop  | 停止Agent             | 
| GET   | /api/v1/users             | 列出所有用户          |
| GET   | /api/v1/projects          | 列出所有项目          |
| GET   | /api/v1/nodes	            | 列出所有Node          |
| POST  | /api/v1/nodes/resources   | 资源上报（供Node调用）| 

### 3.2 Scheduler 服务

#### 3.2.1 职责定义

Scheduler是决策中心，根据任务需求和集群资源状态，选择最合适的Node来部署新的Agent实例。

#### 3.2.2 调度流程

```
1. 接收调度请求
   └── 输入: agent 类型、资源需求(CPU/内存)

2. 过滤阶段 (Filtering)
   ├── 移除不在线的Node
   ├── 移除资源不足的Node
   └── 移除类型不匹配的Node

3. 打分阶段 (Weighting)
   ├── 资源最充裕 (权重 0.7)
   └── 现有Agent数量最少 (权重 0.3)

4. 返回得分最高的Node ID
```

#### 3.2.3 调度策略配置
```toml

[scheduler]
agent_nums_weight = 0.3
cpu_weight = 0.4
memory_weight = 0.3

```

#### 3.2.4 接口定义

| 方法 | 路径 | 功能 |
| :--- | :--- | :--- |
| POST   | /api/v1/schedule         | 输入资源需求，返回最佳Node    | 

### 3.3 Node 服务

#### 3.3.1 职责定义

Node是执行者，运行在每台物理机/虚拟机上，负责Agent实例的完整生命周期管理。对标OpenStack Nova-Compute。

#### 3.3.2 核心模块
| 模块 | 功能 |
| :--- | :--- |
| driver          | 实现具体的agent生命周期管理（例如 OpenCode）|
| resourc monitor | 实时采集本机CPU/内存/磁盘使用率，定期上报Master |

#### 3.3.4 配置
```toml
[node]
# agent 驱动
driver = opencode
# 启动命令
cmd = opencode

```

#### 3.3.5 接口定义

| 方法 | 路径 | 功能 |
| :--- | :--- | :--- |
| POST      | /api/v1/agents            | 创建Agent实例 |
| DELETE    | /api/v1/agents/{id}       | 删除Agent     |


## 4. 关键流程

### 4.1 Agent创建流程

```
用户 → Master: POST /agents (资源需求)
Master → Scheduler: POST /schedule (选Node)
Scheduler → Master: 返回 node-02
Master → Node-02: POST /agents (启动指令)
Node-02: 启动 agent (opencode web)
Node-02 → Master: 返回 Agent信息 (ID,端口)
Master: 更新 agent
Master → 用户: 返回 Agent完整信息
```


## 5. 技术选型
### 5.1 核心框架

| 组件	| 选型方案
| :--- | :--- |
| 编程语言	    | python>=3.12      |
| HTTP框架	    | fastapi           |
| 配置管理	    | pydantic-settings |
| 日志	        | loguru            |
| HTTP客户端	| httpx             |
| ORM	        | sqlmodel          |
| DB	        | sqlite/mysql      |

** 默认使用sqlite