#!/usr/bin/env python3
import os
import json

import aws_cdk as cdk
from ai_ocr_app_2025.ai_ocr_app_2025_stack import FacebookImageStack

# ── プロジェクトルートにある env.json を参照 ────────────────────────────
config_path = os.path.join(os.path.dirname(__file__), "env.json")
try:
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    account         = cfg["account"]
    region          = cfg["region"]
    fb_access_token = cfg["FB_ACCESS_TOKEN"]
    openai_api_key  = cfg["OPENAI_API_KEY"]
    recipient_email = cfg["RECIPIENT_EMAIL"]
except Exception as e:
    raise Exception(f"env.json の読み込みに失敗しました: {e}")
# ──────────────────────────────────────────────────────────────────────────

app = cdk.App()
FacebookImageStack(
    app,
    "FacebookImageStack",
    # FacebookImageStack 側で受け取るパラメータ
    fb_access_token=fb_access_token,
    openai_api_key=openai_api_key,
    recipient_email = recipient_email,
    env=cdk.Environment(account=account, region=region),
    # ▼ 環境非依存スタックにしたい場合は上記 env=... をコメントアウト
)
app.synth()
