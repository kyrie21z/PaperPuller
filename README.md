# PaperPuller

PaperPuller 是一个每日 arXiv 论文拉取和筛选工具，面向 OCR、Scene Text Recognition、ViT、MAE、数据增强等方向。它会从 arXiv 拉取最新论文，用 OpenAI-compatible API 做相关性评分和摘要，结果写入 SQLite，并生成 Markdown 日报。配置 SMTP 后，也可以把日报发送到邮箱。

本项目参考并保留了上游项目 `JoeLeelyf/customize-arxiv-daily`，上游代码放在 `vendor/customize-arxiv-daily`。PaperPuller 自己的配置、数据库、报告、调度脚本和适配层都放在主项目中，避免直接污染上游代码。

## 功能

- 从 arXiv 拉取 `cs.CV`、`cs.AI`、`cs.LG` 等类别论文。
- 使用兴趣描述文件筛选 OCR、STR、ViT、MAE、数据增强相关论文。
- 使用 OpenAI-compatible API 输出评分、标签、推荐理由和 TL;DR。
- 使用 SQLite 保存论文历史、评分结果和邮件发送状态。
- 生成 `reports/YYYY-MM-DD.md` 日报。
- 支持 Gmail、QQ 邮箱等 SMTP 发信。
- 支持 Windows 任务计划程序本地定时运行。
- 提供 GitHub Actions 定时运行模板。

## 目录结构

```text
PaperPuller/
  config/
    interest.md              # 兴趣描述
    paperpuller.yaml         # 主配置
  data/
    papers.sqlite3           # 本地数据库，已被 .gitignore 忽略
  paperpuller/               # 主程序
  reports/                   # 每日 Markdown 日报，已被 .gitignore 忽略
  scripts/
    run_daily.ps1            # Windows 定时任务入口
  tests/                     # 测试
  vendor/
    customize-arxiv-daily/   # 上游参考项目，已被 .gitignore 忽略
```

## 安装

建议使用虚拟环境：

Windows (PowerShell)：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .[dev]
```

Linux / macOS (bash)：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

如果只是运行，不开发测试，也可以用：

```powershell
pip install -e .
```

## 配置 LLM

编辑 `config/paperpuller.yaml`：

```yaml
llm:
  base_url: https://dashscope.aliyuncs.com/compatible-mode/v1
  model: deepseek-v4-flash
  api_key_env: PAPERPULLER_API_KEY
```

`api_key_env` 填环境变量名，不要填真实 API Key。真实 Key 用环境变量设置：

Windows (PowerShell，永久)：

```powershell
[Environment]::SetEnvironmentVariable("PAPERPULLER_API_KEY", "你的API Key", "User")
```

设置后需要重启终端，新的进程才能读到。

Linux / macOS（永久，写入 `~/.bashrc` 或 `~/.zshrc`）：

```bash
echo 'export PAPERPULLER_API_KEY="你的API Key"' >> ~/.bashrc
source ~/.bashrc
```

临时只在当前会话中使用：

Windows (PowerShell)：

```powershell
$env:PAPERPULLER_API_KEY = "你的API Key"
```

Linux / macOS (bash)：

```bash
export PAPERPULLER_API_KEY="你的API Key"
```

## 配置兴趣方向

编辑 `config/interest.md`。默认已经包含：

- OCR 和文档理解
- Scene Text Recognition
- Vision Transformer
- Masked Autoencoder
- 数据增强、合成数据、鲁棒性

如果某些方向不想看，也可以写进排除描述，例如机器人、纯 LLM prompt、医学影像、3D 重建等。

## 配置邮件

在 `config/paperpuller.yaml` 中启用邮件：

```yaml
email:
  enabled: true
  smtp_server: smtp.gmail.com
  smtp_port: 587
  sender: yourname@gmail.com
  receiver: target@example.com
  password_env: PAPERPULLER_SMTP_PASSWORD
  subject: Daily arXiv
```

`password_env` 也只填环境变量名，不要填真实 Gmail App Password。

设置 Gmail App Password：

Windows (PowerShell)：

```powershell
[Environment]::SetEnvironmentVariable("PAPERPULLER_SMTP_PASSWORD", "你的Gmail App Password", "User")
```

Linux / macOS：

```bash
echo 'export PAPERPULLER_SMTP_PASSWORD="你的Gmail App Password"' >> ~/.bashrc
source ~/.bashrc
```

Gmail 的 App Password 通常是 16 位密码，复制时中间可能带空格。程序会自动去掉 Gmail App Password 中的显示空格。

常见 SMTP 配置：

```yaml
# Gmail
smtp_server: smtp.gmail.com
smtp_port: 587

# QQ 邮箱
smtp_server: smtp.qq.com
smtp_port: 587

# 163 邮箱
smtp_server: smtp.163.com
smtp_port: 587
```

Gmail 使用 `587` 时走 STARTTLS，使用 `465` 时走 SSL。

## 常用命令

不发邮件，真实 LLM 小批量测试：

```powershell
python -m paperpuller run --config config/paperpuller.yaml --no-email --max-candidates 1 --fetch-days 30
```

跳过 LLM 和邮件，只测试 arXiv 抓取、SQLite 和报告生成：

```powershell
python -m paperpuller run --config config/paperpuller.yaml --no-email --skip-llm --max-candidates 5 --fetch-days 30
```

正常运行，按配置决定是否发邮件：

```powershell
python -m paperpuller run --config config/paperpuller.yaml
```

重新生成某一天的报告：

```powershell
python -m paperpuller report --config config/paperpuller.yaml --date 2026-06-01
```

运行测试：

```powershell
python -m pytest -q
```

## Windows 定时运行

定时任务入口是：

```powershell
scripts/run_daily.ps1
```

可以在 Windows 任务计划程序中创建每日任务：

- 程序：`powershell.exe`
- 参数：`-ExecutionPolicy Bypass -File C:\Users\52747\Documents\PaperPuller\scripts\run_daily.ps1`
- 起始于：`C:\Users\52747\Documents\PaperPuller`

如果使用用户环境变量保存 API Key 和 SMTP 密码，任务运行时也可以读取。

## Linux 定时运行

定时任务入口是：

```bash
scripts/run_daily.sh
```

### 使用 crontab

编辑 crontab：

```bash
crontab -e
```

添加一行（每天早上 8 点运行，输出写入日志文件）：

```cron
0 8 * * * /home/yourname/PaperPuller/scripts/run_daily.sh >> /home/yourname/PaperPuller/logs/cron.log 2>&1
```

注意：
- 把路径替换为你的实际项目路径。
- crontab 运行时的环境变量较少，如果 API Key 和 SMTP 密码写在 `~/.bashrc` 中，cron 可能读不到。建议在 crontab 文件顶部显式设置：

```cron
PAPERPULLER_API_KEY=你的API Key
PAPERPULLER_SMTP_PASSWORD=你的Gmail App Password
0 8 * * * /home/yourname/PaperPuller/scripts/run_daily.sh >> /home/yourname/PaperPuller/logs/cron.log 2>&1
```

### 使用 systemd timer（可选）

如果希望更灵活的调度（如开机后延迟运行、失败重试），可以创建 systemd service + timer：

`~/.config/systemd/user/paperpuller.service`：

```ini
[Unit]
Description=PaperPuller daily arXiv digest

[Service]
Type=oneshot
ExecStart=%h/PaperPuller/scripts/run_daily.sh
Environment=PAPERPULLER_API_KEY=你的API Key
Environment=PAPERPULLER_SMTP_PASSWORD=你的Gmail App Password
```

`~/.config/systemd/user/paperpuller.timer`：

```ini
[Unit]
Description=PaperPuller daily timer

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
```

启用定时器：

```bash
systemctl --user daemon-reload
systemctl --user enable paperpuller.timer
systemctl --user start paperpuller.timer
```

查看状态：

```bash
systemctl --user status paperpuller.timer
systemctl --user list-timers
```

## GitHub Actions

项目包含 `.github/workflows/daily.yml`，可以在 GitHub 上每天定时运行。

需要在仓库 Secrets 中配置：

- `PAPERPULLER_API_KEY`
- `PAPERPULLER_SMTP_PASSWORD`

如果不希望 GitHub Actions 发邮件，可以在 `config/paperpuller.yaml` 中把 `email.enabled` 改为 `false`。

## 安全注意事项

- 不要把真实 API Key 写入 `config/paperpuller.yaml`。
- 不要把 Gmail App Password 写入 `config/paperpuller.yaml`。
- `data/`、`reports/`、`vendor/customize-arxiv-daily/` 已被 `.gitignore` 忽略。
- 如果密钥曾经被写入文件或终端截图中，建议重新生成。

## 上游项目

如果 `vendor/customize-arxiv-daily` 丢失，可以重新克隆：

```powershell
git clone https://github.com/JoeLeelyf/customize-arxiv-daily.git vendor/customize-arxiv-daily
```
