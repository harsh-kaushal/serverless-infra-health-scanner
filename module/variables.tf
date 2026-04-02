variable "aws_region" {
  type = string
}

variable "aws_account" {
  type = string
}

variable "security_group_ids"{
  type = list(string)
}

variable "subnet_ids"{
  type = list(string)
}

variable "lambda_name"{
  type = string
}

variable "db_suffix"{
  type = string
}

variable "secret_suffix"{
  type = string
}

variable "lambda_log_retention_days"{
  type = string
}

variable "lambda_role_name"{
  type = string
}
variable "max_threads"{
  type = string
}

variable "scan_interval_hours"{
  type = number
  default = 1
}

variable "threshold_minutes"{
  type = number
  default = 0
}

variable "db_alarm_threshold"{
  type = string
}

variable "container_restarts_alarm_threshold"{
  type = string
}
