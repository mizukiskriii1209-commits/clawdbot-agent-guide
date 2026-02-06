# 10. マルチアカウント運用

## ディレクトリ構成

```
~/clawd/
├── .secrets/
│   ├── threads.json              # アカウント1
│   ├── threads-account2.json     # アカウント2
│   ├── threads-account3.json     # アカウント3
│   └── ...
├── threads/                      # アカウント1
├── threads-account2/             # アカウント2
├── threads-account3/             # アカウント3
└── ...
```

## 命名規則

### シークレットファイル

```
.secrets/threads-{username}.json
```

### ディレクトリ

```
threads-{username}/
```

## 新アカウント追加の手順

### 1. Meta Appの設定

1. Meta Developerで新しいアプリを作成
   - または既存アプリにテスターを追加
2. OAuth設定でリダイレクトURLを追加
3. テスターに新アカウントを追加
4. Threads側で招待を承認

### 2. トークン取得

```bash
# 認証URL生成
echo "https://threads.net/oauth/authorize?client_id={APP_ID}&redirect_uri=https://oauth.pstmn.io/v1/callback&scope=threads_basic,threads_content_publish,threads_manage_replies&response_type=code"

# ブラウザでアクセスして認証
# リダイレクトURLからコードを取得

# 短期トークン取得
curl -X POST https://graph.threads.net/oauth/access_token \
  -F client_id={APP_ID} \
  -F client_secret={APP_SECRET} \
  -F grant_type=authorization_code \
  -F redirect_uri=https://oauth.pstmn.io/v1/callback \
  -F code={AUTH_CODE}

# 長期トークン取得
curl -X GET "https://graph.threads.net/access_token?grant_type=th_exchange_token&client_secret={APP_SECRET}&access_token={SHORT_TOKEN}"
```

### 3. シークレットファイル作成

```json
// .secrets/threads-newaccount.json
{
  "app_id": "1234567890",
  "app_secret": "abcdef123456",
  "user_id": "9876543210",
  "username": "new_account",
  "access_token": "LONG_LIVED_TOKEN...",
  "token_type": "long_lived",
  "expires_at": "2026-04-06T00:00:00Z",
  "created_at": "2026-02-05T00:00:00Z",
  "scopes": "threads_basic,threads_content_publish,threads_manage_replies"
}
```

### 4. ディレクトリ作成

```bash
mkdir -p ~/clawd/threads-newaccount/templates
```

### 5. 過去投稿からトンマナ分析

```bash
curl -s -X GET "https://graph.threads.net/v1.0/{USER_ID}/threads?fields=id,text,timestamp&limit=50&access_token={TOKEN}" | jq '.data[].text'
```

### 6. テンプレート作成

分析結果に基づいて200件以上のテンプレートを作成。

### 7. スクリプト設置

`auto_post.py` をコピーして、パスを修正：

```python
BASE_DIR = Path("/root/clawd/threads-newaccount")
SECRETS_FILE = Path("/root/clawd/.secrets/threads-newaccount.json")
```

### 8. systemdタイマー設定

```bash
# サービスファイル作成
sudo nano /etc/systemd/system/threads-newaccount.service

# タイマーファイル作成
sudo nano /etc/systemd/system/threads-newaccount.timer

# 有効化
sudo systemctl daemon-reload
sudo systemctl enable --now threads-newaccount.timer
```

### 9. テスト投稿

```bash
python3 ~/clawd/threads-newaccount/auto_post.py
```

## アカウント一覧管理

### accounts.json

```json
{
  "accounts": [
    {
      "username": "rinna_fukuen",
      "category": "復縁コーチ",
      "posts_per_day": 5,
      "secrets_file": ".secrets/threads.json",
      "directory": "threads"
    },
    {
      "username": "note_kakuzou",
      "category": "40代note挑戦",
      "posts_per_day": 5,
      "secrets_file": ".secrets/threads-kakuzou.json",
      "directory": "threads-kakuzou"
    }
  ]
}
```

## トークン有効期限管理

### 確認スクリプト

```python
#!/usr/bin/env python3
import json
from datetime import datetime
from pathlib import Path

secrets_dir = Path("/root/clawd/.secrets")

for f in secrets_dir.glob("threads*.json"):
    with open(f) as fp:
        data = json.load(fp)
    
    username = data.get("username", "unknown")
    expires = data.get("expires_at", "unknown")
    
    if expires != "unknown":
        exp_date = datetime.fromisoformat(expires.replace("Z", "+00:00"))
        days_left = (exp_date - datetime.now(exp_date.tzinfo)).days
        status = "⚠️" if days_left < 14 else "✅"
    else:
        days_left = "?"
        status = "❓"
    
    print(f"{status} @{username}: {expires} ({days_left} days left)")
```

## 負荷分散

### タイマーの時間をずらす

```ini
# アカウント1: 00分
OnCalendar=*-*-* 08:00:00

# アカウント2: 05分
OnCalendar=*-*-* 08:05:00

# アカウント3: 10分
OnCalendar=*-*-* 08:10:00
```

### RandomizedDelaySecの活用

```ini
# 0〜5分のランダム遅延
RandomizedDelaySec=300
```

## モニタリング

### 全アカウントのログ確認

```bash
for dir in ~/clawd/threads*/; do
  echo "=== $(basename $dir) ==="
  tail -5 "$dir/cron.log" 2>/dev/null || echo "No log"
  echo
done
```

### エラー検出

```bash
grep -r "Error\|error\|failed" ~/clawd/threads*/cron.log
```
