import aws_cdk as core
import aws_cdk.assertions as assertions

from ai_ocr_app_2025.ai_ocr_app_2025_stack import AiOcrApp2025Stack

# example tests. To run these tests, uncomment this file along with the example
# resource in ai_ocr_app_2025/ai_ocr_app_2025_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = AiOcrApp2025Stack(app, "ai-ocr-app-2025")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
