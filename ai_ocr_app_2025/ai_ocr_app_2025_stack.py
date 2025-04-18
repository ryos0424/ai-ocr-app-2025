from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    aws_s3 as s3,
    aws_lambda as _lambda,
    aws_events as events,
    aws_events_targets as targets,
    aws_sns as sns,
    aws_sns_subscriptions as subs,
)
from constructs import Construct


class FacebookImageStack(Stack):
    def __init__(
        self,
        scope: Construct,
        id: str,
        *,
        fb_access_token: str,
        openai_api_key: str,
        recipient_email: str,
        **kwargs,
    ):
        super().__init__(scope, id, **kwargs)

        # ──────────────────────────────────────────────────────
        # 1. 画像保存用 S3 バケット
        # ──────────────────────────────────────────────────────
        bucket = s3.Bucket(
            self,
            "FacebookImageBucket",
            removal_policy=RemovalPolicy.RETAIN,
            event_bridge_enabled=True,
        )

        # ──────────────────────────────────────────────────────
        # 2. 共通 Layer（requests, botocore）
        # ──────────────────────────────────────────────────────
        requests_layer = _lambda.LayerVersion(
            self,
            "RequestsLayer",
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_13],
            code=_lambda.Code.from_asset("layer"),
            description="Layer with requests & botocore",
        )

        # ──────────────────────────────────────────────────────
        # 3. Facebook 画像取得 Lambda
        # ──────────────────────────────────────────────────────
        fetch_fn = _lambda.Function(
            self,
            "FetchFacebookImageFunction",
            runtime=_lambda.Runtime.PYTHON_3_13,
            handler="handler.lambda_handler",
            code=_lambda.Code.from_asset("lambda"),
            timeout=Duration.seconds(300),
            environment={
                "BUCKET_NAME": bucket.bucket_name,
                "FB_ACCESS_TOKEN": fb_access_token,
            },
            layers=[requests_layer],
        )
        bucket.grant_read_write(fetch_fn)

        # 5 分ごとのポーリング
        events.Rule(
            self,
            "PollFacebookPhotosRule",
            schedule=events.Schedule.rate(Duration.minutes(5)),
            targets=[targets.LambdaFunction(fetch_fn)],
        )

        # ──────────────────────────────────────────────────────
        # 4. OCR Orchestrator Lambda
        # ──────────────────────────────────────────────────────
        ocr_fn = _lambda.Function(
            self,
            "OcrOrchestratorFunction",
            runtime=_lambda.Runtime.PYTHON_3_13,
            handler="ocr_orchestrator.lambda_handler",
            code=_lambda.Code.from_asset("lambda_ocr"),
            timeout=Duration.seconds(120),
            environment={
                "BUCKET_NAME": bucket.bucket_name,
                "OPENAI_API_KEY": openai_api_key,
            },
            layers=[requests_layer],
        )
        default_bus = events.EventBus.from_event_bus_name(
            self, "DefaultEventBus", "default"
        )
        default_bus.grant_put_events_to(ocr_fn)
        bucket.grant_read(ocr_fn)

        # S3:ObjectCreated → OCR Lambda
        events.Rule(
            self,
            "S3ObjectCreatedRule",
            event_pattern={
                "source": ["aws.s3"],
                "detail_type": ["Object Created"],
                "detail": {"bucket": {"name": [bucket.bucket_name]}},
            },
            targets=[targets.LambdaFunction(ocr_fn)],
        )

        # ──────────────────────────────────────────────────────
        # 5. SNS トピック & メール購読
        # ──────────────────────────────────────────────────────
        topic = sns.Topic(self, "OcrCalorieTopic")
        topic.add_subscription(
            subs.EmailSubscription(recipient_email)
        )  # 確認メールのリンクをクリックして Confirm すること

        # ──────────────────────────────────────────────────────
        # 6. MailSender Lambda（SNS Publish）
        # ──────────────────────────────────────────────────────
        mail_sender_fn = _lambda.Function(
            self,
            "MailSenderFunction",
            runtime=_lambda.Runtime.PYTHON_3_13,
            handler="mailer.lambda_handler",
            code=_lambda.Code.from_asset("lambda_mailer"),
            timeout=Duration.seconds(10),
            environment={
                "TOPIC_ARN": topic.topic_arn,
            },
            layers=[requests_layer],
        )
        topic.grant_publish(mail_sender_fn)

        # OCRCompleted → MailSender
        events.Rule(
            self,
            "OcrCompletedRule",
            event_pattern={
                "source": ["custom.ocr"],
                "detail_type": ["OCRCompleted"],
            },
            targets=[targets.LambdaFunction(mail_sender_fn)],
        )
