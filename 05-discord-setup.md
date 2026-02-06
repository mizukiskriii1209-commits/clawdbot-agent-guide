# 05. Discord連携設定

## Clawdbot + Discord

ClawdbotはDiscordボットとして動作し、リアルタイムで会話できる。

## 設定手順

### 1. Discord Botを作成

1. https://discord.com/developers/applications にアクセス
2. 「New Application」をクリック
3. 名前を入力してCreate
4. 左メニュー「Bot」→「Add Bot」
5. 「Message Content Intent」を有効化

### 2. Bot Token取得

Bot設定ページで「Reset Token」をクリックしてトークンをコピー。

### 3. Clawdbot設定

config.yamlに追加:

```yaml
discord:
  enabled: true
  bot_token: "YOUR_BOT_TOKEN"
  allowed_guilds:
    - "GUILD_ID_1"
    - "GUILD_ID_2"
  allowed_channels:
    - "CHANNEL_ID_1"
```

### 4. ボットをサーバーに招待

OAuth2 → URL Generatorで:
- Scopes: `bot`, `applications.commands`
- Bot Permissions: `Send Messages`, `Read Message History`, `Add Reactions`

生成されたURLでサーバーに招待。

## チャンネル設定

### メインチャンネル

プライベートな1対1チャンネル。MEMORY.mdを読む。

### グループチャンネル

複数人が参加。メンション時のみ返答。

### タスク管理チャンネル

定期的にタスク状況を投稿。

## Discordでの振る舞い

### メンション対応

```
@Claw2 今日の予定は？
```

→ カレンダーを確認して返答

### リアクション

👍 でサイレント確認
❌ でキャンセル

### コマンド

```
/status - 現在の状態
/help - ヘルプ表示
```

## 注意点

- Discordではマークダウンテーブルが使えない（リスト使用）
- 複数リンクは `<URL>` で囲んでembed抑制
- 長文は分割して送信
