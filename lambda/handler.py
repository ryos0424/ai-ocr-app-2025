import os
import boto3
import requests
from botocore.exceptions import ClientError

BUCKET = os.environ["BUCKET_NAME"]
TOKEN  = os.environ["FB_ACCESS_TOKEN"]
s3     = boto3.client("s3")

def lambda_handler(event, context):
    # 投稿フィードから最新1件の full_picture を取得
    url = (
        "https://graph.facebook.com/v22.0/me/posts"
        "?fields=id,full_picture"
        "&limit=1"
        f"&access_token={TOKEN}"
    )
    resp = requests.get(url)
    resp.raise_for_status()
    body = resp.json()
    data = body.get("data", [])

    if not data or "full_picture" not in data[0]:
        print("No photos found.")
        return

    post = data[0]
    post_id     = post["id"]
    image_url   = post["full_picture"]
    key         = f"{post_id}.jpg"

    # すでに存在するかチェック
    try:
        s3.head_object(Bucket=BUCKET, Key=key)
        print(f"{key} already exists. Skipping.")
        return
    except ClientError as e:
        if e.response["Error"]["Code"] != "404":
            raise

    # ダウンロード＆アップロード
    img_data = requests.get(image_url).content
    s3.put_object(Bucket=BUCKET, Key=key, Body=img_data)
    print(f"Uploaded {key}.")
