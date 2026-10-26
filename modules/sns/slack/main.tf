# Retain the third-party adapter's managed addresses so adopting this source
# updates the deployed function and log group without replacing their identity.
resource "aws_cloudwatch_log_group" "lambda" {
  count             = var.create ? 1 : 0
  name              = "/aws/lambda/${var.lambda_function_name}"
  retention_in_days = 30
  tags              = var.tags
}

resource "aws_sns_topic_subscription" "sns_notify_slack" {
  count     = var.create ? 1 : 0
  topic_arn = var.sns_topic_arn
  protocol  = "lambda"
  endpoint  = module.lambda.lambda_function_arn
}

data "aws_iam_policy_document" "lambda" {
  count = var.create ? 1 : 0
  statement {
    sid       = "AllowWriteToCloudwatchLogs"
    effect    = "Allow"
    actions   = ["logs:CreateLogStream", "logs:PutLogEvents"]
    resources = [replace("${aws_cloudwatch_log_group.lambda[0].arn}:*", ":*:*", ":*")]
  }
}

module "lambda" {
  source                            = "terraform-aws-modules/lambda/aws"
  version                           = "6.4.0"
  create                            = var.create
  function_name                     = var.lambda_function_name
  handler                           = "app.lambda_handler"
  source_path                       = [{ path = "${path.module}/functions/app.py" }]
  recreate_missing_package          = false
  runtime                           = "python3.10"
  timeout                           = 30
  publish                           = true
  layers                            = []
  role_name                         = "lambda-${var.lambda_function_name}"
  attach_cloudwatch_logs_policy     = false
  attach_policy_json                = true
  policy_json                       = try(data.aws_iam_policy_document.lambda[0].json, "")
  use_existing_cloudwatch_log_group = true
  environment_variables = {
    WEBHOOK_URL = var.webhook_url
    MESSENGER   = "slack"
  }
  allowed_triggers = {
    AllowExecutionFromSNS = {
      principal  = "sns.amazonaws.com"
      source_arn = var.sns_topic_arn
    }
  }
  tags       = var.tags
  depends_on = [aws_cloudwatch_log_group.lambda]
}
