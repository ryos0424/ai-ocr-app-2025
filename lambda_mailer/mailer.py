import os
import boto3

# ── 環境変数 ───────────────────────────────────────────────
TOPIC_ARN = os.environ["TOPIC_ARN"]          # CDK から渡される SNS トピック ARN
sns       = boto3.client("sns")              # SNS クライアント
# ────────────────────────────────────────────────────────


def lambda_handler(event, context):
    """
    EventBridge から届いた OCRCompleted イベントを受け取り、
    detail.calories をそのまま SNS トピックへ Publish する。
    Mail アプリで受信 → iOS ショートカットがトリガーされ
    HealthKit に摂取カロリーが書き込まれる想定。
    """

    # ── 1. イベントからカロリー値を取得 ──────────────────
    calories = event.get("detail", {}).get("calories")
    if calories is None:
        print("detail.calories が見つかりません:", event)
        return

    print("受信したカロリー:", calories)

    # ── 2. SNS トピックに Publish ────────────────────────
    sns.publish(
        TopicArn=TOPIC_ARN,
        Subject=f"OCR Calories {calories}",
        Message=f"Calories={calories}",
    )

    print("SNS Publish 完了")
