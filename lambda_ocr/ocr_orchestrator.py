import os
import json
import re
import boto3
from botocore.exceptions import ClientError
from openai import OpenAI

# ── 環境変数 ───────────────────────────────────────────
BUCKET_NAME     = os.environ["BUCKET_NAME"]
OPENAI_API_KEY  = os.environ["OPENAI_API_KEY"]
EVENT_BUS_NAME  = os.environ.get("EVENT_BUS_NAME", "default")
# ────────────────────────────────────────────────────

s3     = boto3.client("s3")
events = boto3.client("events")

# OpenAI クライアント初期化
client = OpenAI(api_key=OPENAI_API_KEY)


def lambda_handler(event, context):
    # 1. S3:ObjectCreated イベントからバケット名／キーを取得
    detail = event.get("detail", {})
    bucket = detail.get("bucket", {}).get("name")
    key    = detail.get("object", {}).get("key")
    if not bucket or not key:
        print("Invalid event detail:", json.dumps(detail))
        return

    # 2. プリサインド URL を発行
    try:
        url = s3.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=3600,
        )
    except ClientError as e:
        print("Error generating presigned URL:", e)
        raise
    print("Presigned URL:", url)

    # 3. OpenAI responses.create で OCR 実行
    try:
        response = client.responses.create(
            model="gpt-4.1-mini",
            input=[{
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": "以下の画像に含まれる文字を抽出し、余計な改行や説明を含まず、テキストのみ返してください。"
                    },
                    {
                        "type":      "input_image",
                        "image_url": url,
                    },
                ],
            }],
        )
    except Exception as e:
        print("OpenAI API request failed:", e)
        raise

    ocr_text = response.output_text.strip()
    print("OCR result:", ocr_text)

    # 4. カロリー値を正規表現で抽出
    m = re.search(
        r"推定消費カロリー\D*?([\d.]+)\s*kcal",
        ocr_text,
        flags=re.IGNORECASE
    )
    if not m:
        print("calorie value not found in OCR text")
        return

    calories = float(m.group(1))
    print("calories =", calories)

    # 5. EventBridge へ OCRCompleted イベント発行
    detail_payload = {
        "bucket":   bucket,
        "key":      key,
        "text":     ocr_text,
        "calories": calories,
    }

    try:
        events.put_events(
            Entries=[{
                "Source":       "custom.ocr",
                "DetailType":   "OCRCompleted",
                "Detail":       json.dumps(detail_payload),
                "EventBusName": EVENT_BUS_NAME,
            }]
        )
        print("Emitted OCRCompleted event")
    except Exception as e:
        print("Failed to emit event:", e)
        raise
