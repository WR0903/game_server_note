---
title: supervisord
category: 未分类
created_at: 2026-08-26 14:36:03
view_count: 3
---

# Supervisord 进程管理手册

> 适用范围：Linux 服务器上非 systemd 托管的常驻进程（业务 server、Python/Node 脚本、队列 worker 等）。
> 参考版本：supervisor 4.x（3.x 差异见文末附录）。

---

## 1. 它解决什么问题

supervisord 是一个用 Python 写的进程管理器，把「前台运行的程序」变成「可托管、可自动拉起、可统一查日志」的服务。

核心价值只有三条：

| 能力 | 说明 |
|---|---|
| 拉起与保活 | 进程退出后按策略自动重启，避免半夜起来手动 `nohup` |
| 统一控制面 | 一个 `supervisorctl` 管住几十个进程，支持分组批量操作 |
| 日志托管 | 自动接管 stdout/stderr，滚动切分，不用业务自己写日志落盘 |

**不适合的场景**：需要 cgroup 资源隔离、需要开机顺序依赖编排、需要 socket 激活 —— 这些交给 systemd。

---

## 2. 安装与初始化

### 2.1 安装

```bash
# 推荐：独立 venv，避免污染系统 Python
python3 -m venv /opt/supervisor
/opt/supervisor/bin/pip install supervisor

# 或者用系统包（版本较旧，但自带 init 脚本）
yum install -y supervisor        # CentOS / TencentOS
apt install -y supervisor        # Debian / Ubuntu
```

### 2.2 生成主配置

```bash
mkdir -p /etc/supervisor/conf.d /var/log/supervisor
/opt/supervisor/bin/echo_supervisord_conf > /etc/supervisor/supervisord.conf
```

### 2.3 主配置骨架

`/etc/supervisor/supervisord.conf`：

```ini
[unix_http_server]
file=/var/run/supervisor.sock
chmod=0700

[supervisord]
logfile=/var/log/supervisor/supervisord.log
logfile_maxbytes=50MB
logfile_backups=10
loglevel=info
pidfile=/var/run/supervisord.pid
nodaemon=false
minfds=65535            ; 打开文件数下限，网络服务务必调大
minprocs=200

[rpcinterface:supervisor]
supervisor.rpcinterface_factory = supervisor.rpcinterface:make_main_rpcinterface

[supervisorctl]
serverurl=unix:///var/run/supervisor.sock

[include]
files = /etc/supervisor/conf.d/*.conf
```

> 一条铁律：**主配置只放全局设置，每个业务一个独立 conf 文件**放进 `conf.d/`。否则改一个服务要动全局文件，回滚代价高。

### 2.4 交给 systemd 托管 supervisord 自己

`/etc/systemd/system/supervisord.service`：

```ini
[Unit]
Description=Supervisor process control system
After=network-online.target
Wants=network-online.target

[Service]
Type=forking
ExecStart=/opt/supervisor/bin/supervisord -c /etc/supervisor/supervisord.conf
ExecReload=/opt/supervisor/bin/supervisorctl reload
ExecStop=/opt/supervisor/bin/supervisorctl shutdown
Restart=on-failure
RestartSec=5
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
```

```bash
systemctl daemon-reload && systemctl enable --now supervisord
```

---

## 3. program 配置详解

一个典型的业务配置 `/etc/supervisor/conf.d/game-server.conf`：

```ini
[program:game-server]
command=/opt/app/bin/game_server --config /opt/app/conf/prod.yaml
directory=/opt/app
user=app
numprocs=1

autostart=true                  ; supervisord 启动时一起拉起
autorestart=unexpected          ; 见下方说明
exitcodes=0                     ; 哪些退出码算「预期退出」
startsecs=5                     ; 存活满 5s 才算启动成功
startretries=3                  ; 启动失败重试次数，超了进 FATAL
stopsignal=TERM                 ; 优雅退出信号
stopwaitsecs=30                 ; 等待优雅退出的秒数，超时发 KILL
stopasgroup=true                ; 信号发给整个进程组
killasgroup=true                ; KILL 也发给整个进程组

stdout_logfile=/var/log/supervisor/game-server.out.log
stdout_logfile_maxbytes=100MB
stdout_logfile_backups=10
redirect_stderr=true            ; stderr 合并进 stdout

environment=PYTHONUNBUFFERED=1,APP_ENV=production
priority=100                    ; 数字小的先启动、后停止
```

### 3.1 高频参数速查

| 参数 | 取值 | 要点 |
|---|---|---|
| `command` | 绝对路径 | **不走 shell**，`&&`、`|`、`*`、`$VAR` 都不生效；需要 shell 就写 `bash -c "..."` |
| `autorestart` | `true` / `false` / `unexpected` | `unexpected` = 只有退出码不在 `exitcodes` 里才重启，最常用 |
| `startsecs` | 秒 | 设为 0 表示「起来就算成功」；服务类程序建议 ≥5，防止崩溃循环被误判成正常 |
| `startretries` | 次 | 重试用退避策略（1s、2s、4s…），耗尽后状态变 `FATAL`，**不再自动恢复** |
| `stopsignal` | `TERM`/`INT`/`QUIT`/`HUP` | 按程序实际处理的信号来。Python 脚本常用 `INT`（触发 KeyboardInterrupt） |
| `stopwaitsecs` | 秒 | 有落盘/收尾逻辑的进程要放宽，默认 10s 常常不够 |
| `numprocs` | 整数 | >1 时必须配 `process_name=%(program_name)s_%(process_num)02d` |
| `priority` | 整数 | 依赖关系用它排序，如 DB 代理 100、业务 200、对外网关 300 |
| `user` | 用户名 | supervisord 以 root 跑时才能降权；**不要让业务裸跑 root** |

### 3.2 多实例 worker

```ini
[program:task-worker]
command=/opt/app/venv/bin/python worker.py --slot %(process_num)d
process_name=%(program_name)s_%(process_num)02d
numprocs=4
numprocs_start=0
directory=/opt/app
autorestart=true
stdout_logfile=/var/log/supervisor/task-worker-%(process_num)02d.log
```

生成 `task-worker_00` ~ `task-worker_03`，可用 `supervisorctl restart 'task-worker:*'` 整体重启。

### 3.3 分组

```ini
[group:game]
programs=game-server,task-worker,match-service
priority=200
```

分组后原来的名字失效，必须用 `game:game-server` 这种全名，批量操作用 `game:*`。

---

## 4. supervisorctl 常用命令

```bash
# 交互模式
supervisorctl

# 状态
supervisorctl status                    # 全部
supervisorctl status game-server        # 单个

# 生命周期
supervisorctl start   game-server
supervisorctl stop    game-server
supervisorctl restart game-server
supervisorctl restart all
supervisorctl restart 'game:*'          # 整组，注意引号防 shell 展开

# 配置变更（重要，见下节）
supervisorctl reread                    # 只读取配置，不生效
supervisorctl update                    # 应用变更：新增的启动、删除的停掉、改过的重启
supervisorctl update game-server        # 只应用某个

# 日志
supervisorctl tail    game-server            # 末尾 1600 字节
supervisorctl tail -f game-server            # 跟随
supervisorctl tail -f game-server stderr     # 看 stderr
supervisorctl clear   game-server            # 清空该程序日志

# 进程信息与信号
supervisorctl pid     game-server
supervisorctl signal  HUP game-server        # 常用于热加载配置
supervisorctl fg      game-server            # 前台附着，调试用，Ctrl-C 会停掉进程！

# 守护进程本身
supervisorctl reload                    # 重启 supervisord，所有子进程会重启 —— 生产慎用
supervisorctl shutdown
```

### `reread / update / reload` 的区别

这是踩坑最多的地方：

- `reread` —— 只是重新读盘并告诉你「哪些变了」，**什么都不做**。
- `update` —— 真正生效，且**只动发生变化的程序**，其他进程不受影响。日常改配置用这个。
- `reload` —— 重启 supervisord 本体，**所有托管进程全部重启**。只在改了 `[supervisord]` 全局段时才用。

日常正确姿势：改完 conf → `reread` 确认 diff → `update`。

---

## 5. 进程状态机

| 状态 | 含义 | 处置 |
|---|---|---|
| `STOPPED` | 已停止（手动停或从未启动） | `start` 拉起 |
| `STARTING` | 已 fork，未满 `startsecs` | 等待 |
| `RUNNING` | 正常运行 | — |
| `BACKOFF` | 启动失败正在重试 | 看日志，通常是配置/依赖问题 |
| `STOPPING` | 收到停止信号，等待退出 | 卡住则检查 `stopsignal` 是否被程序忽略 |
| `EXITED` | 自行退出 | 退出码在 `exitcodes` 内视为正常 |
| `FATAL` | 重试耗尽，放弃 | **不会自愈**，必须人工 `start` |
| `UNKNOWN` | supervisord 内部异常 | 查 supervisord.log |

监控告警只盯两个状态就够：`FATAL` 和 `BACKOFF`。

---

## 6. 日志管理

```ini
stdout_logfile=/var/log/supervisor/app.out.log
stdout_logfile_maxbytes=100MB     ; 设 0 = 不限制大小、不切分（配合外部 logrotate 时用）
stdout_logfile_backups=10         ; 保留份数，0 表示不保留历史
stdout_logfile=AUTO               ; 自动生成到临时目录，不推荐生产用
stdout_logfile=NONE               ; 丢弃
```

要点：

1. **一定要设 `maxbytes` 和 `backups`**，否则磁盘被打满是时间问题。
2. 让 supervisord 自己切分，**不要再叠一层 logrotate**。两者都持有 fd，logrotate 移走文件后 supervisord 会继续往 inode 写，日志凭空消失。真要用 logrotate，必须 `copytruncate`。
3. Python/Node 程序务必关掉输出缓冲，否则日志延迟几分钟才出现：
   - Python：`environment=PYTHONUNBUFFERED=1` 或 `python -u`
   - Node：一般无缓冲问题，但 pino/winston 要确认没开异步 flush

---

## 7. 生产踩坑清单

### 7.1 程序自己 daemon 化了（最高频问题）

supervisord 通过父子关系管进程。程序一旦 fork 到后台，父进程立刻退出，supervisord 认为它「启动即退出」，于是疯狂重启，而真正的进程越堆越多。

**必须让程序前台运行**：

| 程序 | 前台参数 |
|---|---|
| nginx | `daemon off;`（配置里）或 `nginx -g "daemon off;"` |
| php-fpm | `--nodaemonize` |
| gunicorn | 默认前台，不要加 `--daemon` |
| celery | `celery worker`（不要 `--detach`） |
| redis | `daemonize no` |
| 自研程序 | 去掉 fork 逻辑或加 `--foreground` 开关 |

### 7.2 `command` 不是 shell

```ini
# 错：不会生效
command=cd /opt/app && ./run.sh > /dev/null 2>&1

# 对
command=bash -c "cd /opt/app && ./run.sh"
# 更对：用 directory 参数，别塞 shell
directory=/opt/app
command=/opt/app/run.sh
```

同理 `$HOME`、`~`、通配符都不会展开。

### 7.3 环境变量几乎是空的

supervisord 的子进程**不继承你登录 shell 的环境**，`PATH` 也是最小集。所有依赖显式声明：

```ini
environment=PATH="/opt/app/venv/bin:/usr/local/bin:/usr/bin:/bin",LANG="en_US.UTF-8",PYTHONUNBUFFERED="1"
```

值里带逗号或空格要用引号包住。想加载 `.env` 文件，只能靠 `command=bash -c "set -a && . /opt/app/.env && exec ./app"`（注意 `exec`，否则多一层 bash 父进程）。

### 7.4 wrapper 脚本吃掉了信号

如果 `command` 指向一个 shell 脚本，脚本里用 `./app &` 或直接 `./app`（无 exec），supervisord 的 TERM 会打在 bash 上，真实业务进程变孤儿。

```bash
#!/bin/bash
# 脚本最后一行必须 exec，让业务进程替换掉 bash
exec /opt/app/bin/server --config prod.yaml
```

配合 `stopasgroup=true` + `killasgroup=true` 兜底。

### 7.5 FATAL 不会自动恢复

`startretries` 耗尽后进入 `FATAL` 就彻底不管了。监控必须覆盖，或者放宽 `startretries`（比如 999）+ 拉长 `startsecs`。

### 7.6 文件描述符限制

supervisord 的 `minfds` 只是启动检查，真正的限制来自 systemd 的 `LimitNOFILE`。子进程继承 supervisord 的 limit，所以要在 service 文件里设，改 `/etc/security/limits.conf` 对 systemd 拉起的进程无效。

### 7.7 sock 文件权限

```
unix:///var/run/supervisor.sock refused connection
```

多为权限或 supervisord 未运行。让非 root 用户能操作：

```ini
[unix_http_server]
file=/var/run/supervisor.sock
chmod=0770
chown=root:ops        ; 运维组加入 ops 即可用 supervisorctl
```

### 7.8 `/var/run` 重启后被清空

`/var/run` 是 tmpfs。如果配置里写死了子目录（如 `/var/run/supervisor/`），重启后目录不存在导致启动失败。解决：sock 和 pid 直接放 `/var/run/` 下，或用 systemd 的 `RuntimeDirectory=supervisor`。

---

## 8. 常用配置模板

### 8.1 Python 服务

```ini
[program:api]
command=/opt/api/venv/bin/gunicorn -w 4 -b 127.0.0.1:8000 app:application
directory=/opt/api
user=app
environment=PYTHONUNBUFFERED="1",PATH="/opt/api/venv/bin:%(ENV_PATH)s"
autostart=true
autorestart=unexpected
startsecs=10
stopsignal=TERM
stopwaitsecs=30
stopasgroup=true
killasgroup=true
redirect_stderr=true
stdout_logfile=/var/log/supervisor/api.log
stdout_logfile_maxbytes=100MB
stdout_logfile_backups=7
```

### 8.2 长连接游戏服（优雅停机）

```ini
[program:gs]
command=/opt/gs/bin/gameserver -id 1
directory=/opt/gs
user=game
autorestart=unexpected
exitcodes=0,2                 ; 2 = 主动热更新退出，不重启
startsecs=15
stopsignal=QUIT               ; 程序内捕获 QUIT 做玩家存盘
stopwaitsecs=120              ; 存盘慢，给足时间
priority=200
redirect_stderr=true
stdout_logfile=/var/log/supervisor/gs.log
stdout_logfile_maxbytes=200MB
stdout_logfile_backups=20
```

### 8.3 一次性任务 / 数据迁移

```ini
[program:migrate]
command=/opt/app/venv/bin/python migrate.py
autostart=false                ; 不随 supervisord 启动
autorestart=false              ; 跑完就完
startsecs=0                    ; 秒退也算成功
exitcodes=0
redirect_stderr=true
stdout_logfile=/var/log/supervisor/migrate.log
```

用 `supervisorctl start migrate` 手动触发，`EXITED` 是正常终态。

---

## 9. 监控与巡检

### 9.1 快速巡检脚本

```bash
#!/bin/bash
# 输出所有非 RUNNING 的进程，用于告警
supervisorctl status | awk '$2 != "RUNNING" {print}' | grep -v '^$'
```

### 9.2 XML-RPC 采集（推荐做法）

```python
from xmlrpc.client import ServerProxy
import supervisor.xmlrpc, http.client

# 走 unix socket
tp = supervisor.xmlrpc.SupervisorTransport(None, None, 'unix:///var/run/supervisor.sock')
s = ServerProxy('http://127.0.0.1', transport=tp)

for p in s.supervisor.getAllProcessInfo():
    print(p['group'], p['name'], p['statename'], p['pid'], p['description'])
```

关键字段：`statename`、`pid`、`start`（启动时间戳）、`exitstatus`、`spawnerr`。用 `start` 可以算出「近 N 分钟内重启过」这类频繁重启告警。

### 9.3 开启 HTTP 面板（内网 only）

```ini
[inet_http_server]
port=127.0.0.1:9001
username=admin
password={SHA}xxxxxxxx        ; echo -n 'pwd' | sha1sum
```

**绝不要监听 0.0.0.0**。这个接口等于远程任意命令执行，历史上被挖矿蠕虫批量打过。要外部访问就走 nginx 反代 + IP 白名单。

---

## 10. 故障排查路径

```
进程没起来
├─ supervisorctl status 看状态
│  ├─ FATAL   → supervisorctl tail <name> stderr，看 spawnerr
│  ├─ BACKOFF → 启动即退出，99% 是 daemon 化 / 路径 / 权限 / 端口占用
│  └─ EXITED  → 检查 exitcodes 与 autorestart 配置
├─ 日志为空
│  ├─ 输出缓冲未关（PYTHONUNBUFFERED）
│  ├─ 程序自己重定向了 stdout 到别处
│  └─ logfile 目录不存在或无写权限
├─ 命令行手跑正常，supervisor 下失败
│  └─ 必然是环境差异：PATH / 环境变量 / user / cwd / ulimit
└─ stop 卡住不退
   ├─ stopsignal 程序未处理
   ├─ wrapper 脚本没用 exec
   └─ 加 stopasgroup + killasgroup，缩短 stopwaitsecs
```

诊断三连：

```bash
tail -100 /var/log/supervisor/supervisord.log     # 守护进程视角
supervisorctl tail -100 <name> stderr             # 业务视角
ps -ef --forest | grep -A3 supervisord            # 进程树，看有没有多余父进程
```

---

## 11. 与 systemd 的取舍

| 维度 | supervisord | systemd |
|---|---|---|
| 多实例批量管理 | 强，分组 + 通配符 | 需 template unit，较繁琐 |
| 非 root 用户自管 | 支持，装在自己家目录即可 | 需 user session,受限 |
| 资源限制 (cgroup) | 无 | 原生支持 |
| 启动依赖编排 | 只有 priority 排序 | After/Requires 完整依赖 |
| 日志 | 直接落文件，好排查 | journald，需 journalctl |
| 容器内使用 | 常用（管理多进程） | 基本不可用 |
| 配置热更新 | `update` 只重启变更项 | `daemon-reload` + restart |

实践建议：**系统级基础组件用 systemd，业务应用（尤其多实例、需要频繁重启发布的）用 supervisord**，并把 supervisord 本身交给 systemd 托管。

---

## 附录 A：3.x vs 4.x 差异

- 3.x 只支持 Python 2，4.x 起支持 Python 3（4.2+ 要求 ≥3.4）。
- 4.x 修正了 `logfile_maxbytes` 在部分场景不生效的问题。
- 3.x 的 `supervisorctl` 对 group 通配符支持不完整，建议直接上 4.x。
- 系统包（yum/apt）常常还是 3.x，生产建议 pip 装 4.x。

## 附录 B：目录规范建议

```
/etc/supervisor/
├── supervisord.conf          # 只有全局段
└── conf.d/
    ├── game-server.conf
    ├── task-worker.conf
    └── migrate.conf
/var/log/supervisor/
├── supervisord.log           # 守护进程自身
└── <program>.log             # 每个程序独立
/opt/supervisor/              # venv 安装位置
```

配置文件纳入 Git 或配置管理（Ansible/SaltStack），`conf.d` 目录整体分发，变更后统一 `reread && update`。

## 附录 C：一页速查

```bash
# 日常
supervisorctl status
supervisorctl restart 'group:*'
supervisorctl reread && supervisorctl update
supervisorctl tail -f <name>

# 排查
supervisorctl status | grep -v RUNNING
tail -f /var/log/supervisor/supervisord.log
ps -ef --forest | grep supervisord

# 必查配置项
autorestart=unexpected   startsecs>=5    stopasgroup=true
maxbytes+backups 已设     程序为前台运行    user 非 root
```