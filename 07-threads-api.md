# 07. Threads API認証

## 概要

Threads APIはMeta公式のAPI。2024年6月に公開。
自動投稿、リプライ管理、インサイト取得が可能。

## 必要なもの

1. **Meta Developerアカウント**
   - https://developers.facebook.com/
   - 2FA有効化必須

2. **Threadsアカウント**
   - API経由で投稿したいアカウント

3. **Meta App**
   - 「Access the Threads API」を選択して作成

## セットアップ手順

### Step 1: Meta Developerでアプリ作成

1. https://developers.facebook.com/apps/creation/ にアクセス
2. 「Access the Threads API」を選択
3. アプリ名とメールアドレスを入力

### Step 2: 権限設定

App Dashboard → Use cases → Customize で以下を追加：

| Scope | 用途 |
|-------|------|
| `threads_basic` | 基本アクセス（必須） |
| `threads_content_publish` | 投稿の作成・公開 |
| `threads_manage_replies` | リプライの管理 |

### Step 3: OAuth設定

Settings タブで Redirect Callback URLs を設定：

```
https://oauth.pstmn.io/v1/callback
```

これはPostmanのコールバックURL。実際のアプリがなくても認証できる。

### Step 4: テスターを追加

1. App roles → Roles → Testers タブ
2. 「Add People」→「Threads Tester」を選択
3. Threadsのユーザー名を入力

### Step 5: 招待を承認

Threads側で：
1. https://www.threads.net/settings/account にアクセス
2. Website permissions → Invites タブ
3. 招待を承認

### Step 6: アクセストークン取得

#### 6-1. 認証コード取得

ブラウザで以下URLにアクセス：

```
https://threads.net/oauth/authorize?client_id={APP_ID}&redirect_uri=https://oauth.pstmn.io/v1/callback&scope=threads_basic,threads_content_publish,threads_manage_replies&response_type=code
```

認証後、リダイレクトURLに `code=XXXXX` が含まれる。

#### 6-2. 短期トークン取得

```bash
curl -X POST https://graph.threads.net/oauth/access_token \
  -F client_id={APP_ID} \
  -F client_secret={APP_SECRET} \
  -F grant_type=authorization_code \
  -F redirect_uri=https://oauth.pstmn.io/v1/callback \
  -F code={AUTH_CODE}
```

レスポンス：
```json
{
  "access_token": "THQVJ...",
  "user_id": 12345678
}
```

#### 6-3. 長期トークン取得（60日有効）

```bash
curl -X GET "https://graph.threads.net/access_token?grant_type=th_exchange_token&client_secret={APP_SECRET}&access_token={SHORT_LIVED_TOKEN}"
```

レスポンス：
```json
{
  "access_token": "LONG_LIVED_TOKEN...",
  "token_type": "bearer",
  "expires_in": 5184000
}
```

### Step 7: トークンを保存

```json
// .secrets/threads-{account}.json
{
  "app_id": "1234567890",
  "app_secret": "abcdef123456",
  "user_id": "9876543210",
  "username": "your_username",
  "access_token": "LONG_LIVED_TOKEN...",
  "token_type": "long_lived",
  "expires_at": "2026-04-06T00:00:00Z",
  "created_at": "2026-02-05T00:00:00Z",
  "scopes": "threads_basic,threads_content_publish,threads_manage_replies"
}
```

## トークン更新

長期トークンは60日で期限切れ。期限前に更新：

```bash
curl -X GET "https://graph.threads.net/refresh_access_token?grant_type=th_refresh_token&access_token={LONG_LIVED_TOKEN}"
```

### 自動更新の仕組み

cronで定期的にトークンをチェック・更新：

```bash
# 毎週日曜日にトークン更新チェック
0 0 * * 0 /path/to/refresh_tokens.py
```

## API使用例

### プロフィール取得

```bash
curl -X GET "https://graph.threads.net/v1.0/me?fields=id,username,threads_profile_picture_url,threads_biography&access_token={ACCESS_TOKEN}"
```

### 投稿（2段階）

```bash
# Step 1: メディアコンテナ作成
curl -X POST "https://graph.threads.net/v1.0/{USER_ID}/threads" \
  -d "media_type=TEXT" \
  -d "text=Hello World" \
  -d "access_token={ACCESS_TOKEN}"

# レスポンス: {"id": "CONTAINER_ID"}

# Step 2: 公開
curl -X POST "https://graph.threads.net/v1.0/{USER_ID}/threads_publish" \
  -d "creation_id={CONTAINER_ID}" \
  -d "access_token={ACCESS_TOKEN}"

# レスポンス: {"id": "POST_ID"}
```

### リプライ投稿

```bash
curl -X POST "https://graph.threads.net/v1.0/{USER_ID}/threads" \
  -d "media_type=TEXT" \
  -d "text=This is a reply" \
  -d "reply_to_id={PARENT_POST_ID}" \
  -d "access_token={ACCESS_TOKEN}"
```

## トラブルシューティング

### 認証エラー

```
URLはブロックされています: リダイレクトURIがホワイトリストにない
```

→ Meta DeveloperでリダイレクトURLを設定する

### トークン期限切れ

```
Error validating access token: Session has expired
```

→ 再認証してトークンを取得し直す

### 権限不足

```
(#10) This endpoint requires the 'threads_content_publish' permission
```

→ App Dashboardで権限を追加し、再認証する
