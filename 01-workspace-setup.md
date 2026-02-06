# 01. ワークスペース構成

## 推奨ディレクトリ構造

```
~/clawd/                          # ワークスペースルート
├── AGENTS.md                     # 行動規範（必須）
├── SOUL.md                       # 人格設定（必須）
├── USER.md                       # ユーザー情報（必須）
├── TOOLS.md                      # ツール設定メモ
├── IDENTITY.md                   # アイデンティティ
├── HEARTBEAT.md                  # 定期タスク設定
├── MEMORY.md                     # 長期記憶（メインセッション用）
├── memory/                       # 日次メモリ
│   ├── 2026-01-26.md
│   ├── 2026-01-27.md
│   └── ...
├── .secrets/                     # 認証情報（.gitignore推奨）
│   ├── threads.json
│   ├── threads-account2.json
│   └── ...
├── knowledge/                    # ナレッジベース
│   ├── threads-api.md
│   └── ...
├── threads/                      # Threadsアカウント1
│   ├── auto_post.py
│   ├── templates.json
│   ├── post_log.json
│   └── cron.log
├── threads-account2/             # Threadsアカウント2
│   └── ...
└── projects/                     # その他のプロジェクト
    └── ...
```

## 重要なファイルの役割

### 必須ファイル

| ファイル | 役割 |
|---------|------|
| `AGENTS.md` | エージェントの行動規範。毎セッション読み込む |
| `SOUL.md` | 人格・トーン設定。どんな存在であるか |
| `USER.md` | ユーザー情報。名前、呼び方、タイムゾーン等 |

### 推奨ファイル

| ファイル | 役割 |
|---------|------|
| `IDENTITY.md` | 名前、種族、絵文字、アバター等 |
| `TOOLS.md` | 環境固有のツール設定メモ |
| `HEARTBEAT.md` | 定期実行するタスクのチェックリスト |
| `MEMORY.md` | 長期記憶。重要な情報を蓄積 |

## .gitignore 推奨設定

```gitignore
# 認証情報
.secrets/

# ログファイル
*.log
cron.log

# 一時ファイル
*.tmp
__pycache__/

# 投稿ログ（大きくなるため）
post_log.json
posted_ids.json
```

## ワークスペースの初期化

```bash
# ディレクトリ作成
mkdir -p ~/clawd/{memory,.secrets,knowledge}

# 基本ファイル作成
touch ~/clawd/{AGENTS.md,SOUL.md,USER.md,IDENTITY.md,TOOLS.md}

# memory ディレクトリに今日のファイル
touch ~/clawd/memory/$(date +%Y-%m-%d).md
```

## 権限設定

```bash
# .secrets は自分だけ読み書き可能に
chmod 700 ~/clawd/.secrets
chmod 600 ~/clawd/.secrets/*
```
