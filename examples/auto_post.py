#!/usr/bin/env python3
"""
Threads自動投稿スクリプト（汎用版）
5投稿に1回リプライでプロモーション

使い方:
1. BASE_DIR と SECRETS_FILE のパスを変更
2. templates.json を作成
3. systemd timer で定期実行
"""

import json
import random
import requests
import time
from datetime import datetime
from pathlib import Path

# ========================================
# 設定 - ここを変更
# ========================================
BASE_DIR = Path("/root/clawd/threads-account")
SECRETS_FILE = Path("/root/clawd/.secrets/threads-account.json")
# ========================================

TEMPLATES_FILE = BASE_DIR / "templates.json"
POST_LOG_FILE = BASE_DIR / "post_log.json"
POSTED_IDS_FILE = BASE_DIR / "posted_ids.json"
POST_COUNT_FILE = BASE_DIR / "post_count.json"


def load_secrets():
    """認証情報を読み込む"""
    with open(SECRETS_FILE) as f:
        return json.load(f)


def load_templates():
    """テンプレートとプロモテキストを読み込む"""
    if TEMPLATES_FILE.exists():
        with open(TEMPLATES_FILE) as f:
            data = json.load(f)
        
        # 形式の自動判定
        if isinstance(data, list):
            # シンプル形式: [{"text": "..."}, ...]
            return data, []
        else:
            # 拡張形式: {"templates": [...], "promo_texts": [...]}
            return data.get("templates", []), data.get("promo_texts", [])
    return [], []


def load_posted_ids():
    """投稿済みIDを読み込む"""
    if POSTED_IDS_FILE.exists():
        with open(POSTED_IDS_FILE) as f:
            return set(json.load(f))
    return set()


def save_posted_ids(ids):
    """投稿済みIDを保存"""
    with open(POSTED_IDS_FILE, "w") as f:
        json.dump(list(ids), f)


def load_post_count():
    """投稿カウントを読み込む"""
    if POST_COUNT_FILE.exists():
        with open(POST_COUNT_FILE) as f:
            return json.load(f).get("count", 0)
    return 0


def save_post_count(count):
    """投稿カウントを保存"""
    with open(POST_COUNT_FILE, "w") as f:
        json.dump({"count": count}, f)


def load_post_log():
    """投稿ログを読み込む"""
    if POST_LOG_FILE.exists():
        with open(POST_LOG_FILE) as f:
            return json.load(f)
    return {"posts": []}


def save_post_log(log):
    """投稿ログを保存"""
    with open(POST_LOG_FILE, "w") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)


def post_to_threads(text, secrets, reply_to_id=None):
    """
    Threadsに投稿（2段階プロセス）
    
    Args:
        text: 投稿内容
        secrets: 認証情報
        reply_to_id: リプライ先の投稿ID（オプション）
    
    Returns:
        投稿ID または None（失敗時）
    """
    user_id = secrets["user_id"]
    access_token = secrets["access_token"]

    # Step 1: メディアコンテナ作成
    create_url = f"https://graph.threads.net/v1.0/{user_id}/threads"
    create_params = {
        "media_type": "TEXT",
        "text": text,
        "access_token": access_token,
    }
    if reply_to_id:
        create_params["reply_to_id"] = reply_to_id

    resp = requests.post(create_url, data=create_params)
    if resp.status_code != 200:
        print(f"Error creating container: {resp.status_code} {resp.text}")
        return None

    container_id = resp.json()["id"]
    print(f"Container created: {container_id}")

    # 処理待ち（推奨: 3秒）
    time.sleep(3)

    # Step 2: 公開
    publish_url = f"https://graph.threads.net/v1.0/{user_id}/threads_publish"
    publish_params = {
        "creation_id": container_id,
        "access_token": access_token,
    }

    resp = requests.post(publish_url, data=publish_params)
    if resp.status_code != 200:
        print(f"Error publishing: {resp.status_code} {resp.text}")
        return None

    post_id = resp.json()["id"]
    print(f"Posted successfully! ID: {post_id}")
    return post_id


def main():
    print(f"=== Threads Auto Post: {datetime.now().isoformat()} ===")
    
    secrets = load_secrets()
    templates, promo_texts = load_templates()
    posted_ids = load_posted_ids()
    post_count = load_post_count()

    # 未投稿のテンプレートを選択
    available = []
    for t in templates:
        template_id = t.get("id", templates.index(t))
        if template_id not in posted_ids:
            available.append({"id": template_id, "text": t["text"]})

    # 全部使い切ったらリセット
    if not available:
        print("All templates posted. Resetting...")
        posted_ids = set()
        available = [{"id": t.get("id", i), "text": t["text"]} 
                     for i, t in enumerate(templates)]

    # ランダム選択
    selected = random.choice(available)
    text = selected["text"]
    template_id = selected["id"]

    print(f"Template ID: {template_id}")
    print(f"Text: {text[:80]}...")

    # メイン投稿
    post_id = post_to_threads(text, secrets)

    if post_id:
        # 投稿済みに追加
        posted_ids.add(template_id)
        save_posted_ids(posted_ids)

        # カウント更新
        post_count += 1
        save_post_count(post_count)

        # ログに記録
        log = load_post_log()
        log_entry = {
            "id": post_id,
            "template_id": template_id,
            "text": text,
            "timestamp": datetime.now().isoformat(),
        }

        # 5投稿に1回、リプライでプロモーション
        if post_count % 5 == 0 and promo_texts:
            print("Adding promo reply...")
            time.sleep(5)
            promo_text = random.choice(promo_texts)
            reply_id = post_to_threads(promo_text, secrets, reply_to_id=post_id)
            if reply_id:
                log_entry["promo_reply_id"] = reply_id
                log_entry["promo_text"] = promo_text
                print(f"Promo reply added! ID: {reply_id}")

        log["posts"].append(log_entry)
        save_post_log(log)

        print(f"Post count: {post_count} (promo every 5th)")
        print(f"Remaining templates: {len(templates) - len(posted_ids)}")
    else:
        print("Failed to post.")


if __name__ == "__main__":
    main()
