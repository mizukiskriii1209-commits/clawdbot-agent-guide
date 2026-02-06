# 08. 自動投稿システム構築

## システム構成

```
.secrets/threads-{account}.json   # 認証情報
threads-{account}/
├── auto_post.py                  # 投稿スクリプト
├── templates.json                # テンプレート
├── posted_ids.json               # 投稿済みID
├── post_count.json               # 投稿カウント
├── post_log.json                 # 投稿ログ
└── cron.log                      # 実行ログ
```

## 自動投稿スクリプト

### 基本版（シンプル）

```python
#!/usr/bin/env python3
"""
Threads自動投稿スクリプト（基本版）
"""

import json
import random
import requests
import time
from datetime import datetime
from pathlib import Path

BASE_DIR = Path("/root/clawd/threads-account")
SECRETS_FILE = Path("/root/clawd/.secrets/threads-account.json")
TEMPLATES_FILE = BASE_DIR / "templates.json"
POST_LOG_FILE = BASE_DIR / "post_log.json"
POSTED_IDS_FILE = BASE_DIR / "posted_ids.json"


def load_secrets():
    with open(SECRETS_FILE) as f:
        return json.load(f)


def load_templates():
    if TEMPLATES_FILE.exists():
        with open(TEMPLATES_FILE) as f:
            return json.load(f)
    return []


def load_posted_ids():
    if POSTED_IDS_FILE.exists():
        with open(POSTED_IDS_FILE) as f:
            return set(json.load(f))
    return set()


def save_posted_ids(ids):
    with open(POSTED_IDS_FILE, "w") as f:
        json.dump(list(ids), f)


def load_post_log():
    if POST_LOG_FILE.exists():
        with open(POST_LOG_FILE) as f:
            return json.load(f)
    return {"posts": []}


def save_post_log(log):
    with open(POST_LOG_FILE, "w") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)


def post_to_threads(text, secrets):
    """Threadsに投稿（2段階）"""
    user_id = secrets["user_id"]
    access_token = secrets["access_token"]

    # Step 1: コンテナ作成
    create_url = f"https://graph.threads.net/v1.0/{user_id}/threads"
    create_params = {
        "media_type": "TEXT",
        "text": text,
        "access_token": access_token
    }

    resp = requests.post(create_url, data=create_params)
    if resp.status_code != 200:
        print(f"Error creating container: {resp.text}")
        return None

    container_id = resp.json()["id"]
    print(f"Container created: {container_id}")

    # 処理待ち
    time.sleep(3)

    # Step 2: 公開
    publish_url = f"https://graph.threads.net/v1.0/{user_id}/threads_publish"
    publish_params = {
        "creation_id": container_id,
        "access_token": access_token
    }

    resp = requests.post(publish_url, data=publish_params)
    if resp.status_code != 200:
        print(f"Error publishing: {resp.text}")
        return None

    post_id = resp.json()["id"]
    print(f"Posted successfully! ID: {post_id}")
    return post_id


def main():
    secrets = load_secrets()
    templates = load_templates()
    posted_ids = load_posted_ids()

    # 未投稿のテンプレートを選択
    available = []
    for i, t in enumerate(templates):
        template_id = f"template_{i}"
        if template_id not in posted_ids:
            available.append({"id": template_id, "text": t["text"]})

    # 全部使い切ったらリセット
    if not available:
        print("All templates posted. Resetting...")
        posted_ids = set()
        available = [{"id": f"template_{i}", "text": t["text"]} 
                     for i, t in enumerate(templates)]

    # ランダム選択
    selected = random.choice(available)
    text = selected["text"]

    print(f"Template ID: {selected['id']}")
    print(f"Text: {text}")

    # 投稿
    post_id = post_to_threads(text, secrets)

    if post_id:
        # 投稿済みに追加
        posted_ids.add(selected["id"])
        save_posted_ids(posted_ids)

        # ログに記録
        log = load_post_log()
        log["posts"].append({
            "id": post_id,
            "template_id": selected["id"],
            "text": text,
            "timestamp": datetime.now().isoformat()
        })
        save_post_log(log)

        print(f"Total posts: {len(log['posts'])}")


if __name__ == "__main__":
    main()
```

### 拡張版（リプライでプロモーション）

```python
# 5投稿に1回、リプライでnote誘導を追加

POST_COUNT_FILE = BASE_DIR / "post_count.json"

PROMO_TEXTS = [
    "詳しくはnoteで公開中👇\nhttps://note.com/your_account/n/xxx",
    "もっと知りたい方はこちら👇\nhttps://note.com/your_account/n/xxx",
]

def load_post_count():
    if POST_COUNT_FILE.exists():
        with open(POST_COUNT_FILE) as f:
            return json.load(f).get("count", 0)
    return 0

def save_post_count(count):
    with open(POST_COUNT_FILE, "w") as f:
        json.dump({"count": count}, f)

def post_to_threads_with_reply(text, secrets, reply_to_id=None):
    # 上記と同じ、reply_to_id パラメータを追加
    ...

# main() 内で
post_count = load_post_count()
post_id = post_to_threads(text, secrets)

if post_id:
    post_count += 1
    save_post_count(post_count)

    # 5投稿に1回、プロモーション
    if post_count % 5 == 0:
        time.sleep(5)
        promo_text = random.choice(PROMO_TEXTS)
        post_to_threads_with_reply(promo_text, secrets, reply_to_id=post_id)
```

## systemdタイマー設定

### サービスファイル

```ini
# /etc/systemd/system/threads-account.service
[Unit]
Description=Threads auto post for account
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/bin/python3 /root/clawd/threads-account/auto_post.py
WorkingDirectory=/root/clawd/threads-account
StandardOutput=append:/root/clawd/threads-account/cron.log
StandardError=append:/root/clawd/threads-account/cron.log
```

### タイマーファイル

```ini
# /etc/systemd/system/threads-account.timer
[Unit]
Description=Threads auto post timer (5x daily)

[Timer]
OnCalendar=*-*-* 08:00:00
OnCalendar=*-*-* 12:30:00
OnCalendar=*-*-* 18:00:00
OnCalendar=*-*-* 21:00:00
OnCalendar=*-*-* 23:00:00
Persistent=true
RandomizedDelaySec=300

[Install]
WantedBy=timers.target
```

### 有効化

```bash
sudo systemctl daemon-reload
sudo systemctl enable threads-account.timer
sudo systemctl start threads-account.timer

# 確認
sudo systemctl status threads-account.timer
```

## 投稿頻度の目安

| アカウントタイプ | 推奨投稿数 |
|-----------------|----------|
| 成長フェーズ | 5-7回/日 |
| 維持フェーズ | 3-5回/日 |
| 低アクティブ | 1-3回/日 |

## ログの確認

```bash
# 最新のログを確認
tail -50 /root/clawd/threads-account/cron.log

# エラーを抽出
grep -i error /root/clawd/threads-account/cron.log
```
