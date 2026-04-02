# 🚑 Autonomous Infrastructure Health Scanner

**Lightweight reliability monitoring for cloud infrastructure — automated, observable, and production-ready.**

---

## 🧭 What is it

The **Autonomous Infrastructure Health Scanner** is a drop-in serverless component that continuously checks the health of your infrastructure and surfaces early warning signals.

It automatically scans:

🗄️ **PostgreSQL databases** → Detects long-running (stuck) queries
📦 **Kubernetes workloads** → Detects abnormal container restart spikes via Prometheus
📊 **CloudWatch metrics** → Triggers alerts before incidents escalate

**Design goals:**

⚡ Fast detection
🔁 Fully automated
🔐 Secure by default
🧩 Easy to integrate
🏗️ Infrastructure-as-Code friendly

---

## 📦 How to get it

### Step 1 — Clone the repository

```
git clone https://github.com/your-repo/autonomous-infrastructure-health-scanner.git
cd autonomous-infrastructure-health-scanner
```

### Step 2 — Initialize Terraform

```
terraform init
```

### Step 3 — Deploy the infrastructure

```
terraform apply
```

---

### What gets created automatically

⚙️ Lambda function
⏰ EventBridge scheduled trigger
📊 CloudWatch custom metrics
🚨 CloudWatch alarms
🔐 IAM roles and permissions

**No manual wiring required.**

---

## 🛠️ How to implement it in your project

This scanner is designed to plug into existing infrastructure with minimal changes.

---

### Step 1 — Follow simple naming conventions

Your resources should follow predictable patterns so the scanner can auto-discover them.

```
<service>-connect
<service>-connect-db-secret
<service>-alb
```

**Example:**

```
payments-connect
payments-connect-db-secret
payments-alb
```

---

### Step 2 — Store database credentials in Secrets Manager

**Required secret structure:**

```
{
  "username": "app_user",
  "rds_password": "password",
  "host": "db.endpoint.amazonaws.com",
  "dbname": "application",
  "engine": "postgres"
}
```

🔐 Credentials are retrieved dynamically — nothing is hardcoded.

---

### Step 3 — Expose a Prometheus endpoint

Your cluster should expose Prometheus metrics behind an internal ALB.

```
https://internal-service-alb/prometheus/api/v1/query
```

This allows the scanner to detect container instability patterns.

---

### Step 4 — Deploy the Terraform module

```
module "health_scanner" {
  source = "./module"

  threshold_minutes = 90
  max_threads       = 10
}
```

---

## 🔄 What happens after deployment

Every scheduled run:

1️⃣ Discover databases automatically
2️⃣ Fetch credentials securely
3️⃣ Detect long-running queries
4️⃣ Query Prometheus for restart spikes
5️⃣ Publish CloudWatch metrics
6️⃣ Trigger alerts if thresholds are exceeded

**No dashboards required. No manual checks.**

---

## 🎯 Typical Use Cases

* Detect stuck database queries before performance degradation
* Identify crashing or unstable containers
* Add proactive alerting to production systems
* Improve platform reliability
* Strengthen observability without heavy tooling

---

## 💡 Why this exists

Most monitoring systems react **after failure**.

This scanner focuses on detecting **early instability signals**, enabling teams to respond before incidents escalate into outages.

It is intentionally:

🪶 Lightweight
🤖 Automated
🔍 Observable
🏭 Production-focused
