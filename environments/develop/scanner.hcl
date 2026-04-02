terraform {
  source = "../../module"
}

remote_state {
  backend = "s3"
  config = {
    region = "us-west-2"
    bucket = "health-scanner-<TARGET_ACCOUNT>-tfstate"
    key    = "health-scanner-<TARGET_ACCOUNT>-tfstat"e"
    dynamodb_table = "health-scanner-<TARGET_ACCOUNT>-tfstate"
    disable_bucket_update = true
  }
}

inputs = {
  aws_region = "us-west-2"
  aws_account = "XXXXXXXXX"
  vpc_id      = "vpc-xxxxxxxxxx"
  subnet_ids = ["","",""]
  security_group_ids = ["sg-xxxxxxxx"]
}