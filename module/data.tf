data "external" "zip_lambda_build" {
    program = ["bash", "${path.module}/lambda/build.sh"]
}