# ai-ocr-app-2025
Facebookに投稿した画像の最新一枚を5分ごとに取得、  
OPENAI_APIでOCR処理し、iphoneにメールする。

# env.jsonに必要な変数
"account":  
"region":  
"FB_ACCESS_TOKEN":  
"OPENAI_API_KEY":  
"RECIPIENT_EMAIL":  

# Lambda Layerについて
layer/requirements-layer.txtをダウンロードして、  
layer/pythonに入れておく必要がある。  
　※デプロイ時のダウンロードは未実装  
