# 🚑 Serverless Infrastructure Health Scanner

**Lightweight, cost-efficient reliability monitoring for cloud infrastructure — automated, observable, and production-ready.**

---

## 🧭 What is it

The **Serverless Infrastructure Health Scanner** is a drop-in serverless component that continuously checks the health of your infrastructure and surfaces early warning signals before incidents escalate.

It automatically scans:

🗄️ **PostgreSQL databases** → Detects long-running (stuck) queries
📦 **Kubernetes workloads** → Detects abnormal container restart spikes via Prometheus
📊 **CloudWatch metrics** → Publishes health signals and triggers alerts

**Design goals**

⚡ Fast detection
🔁 Fully automated
🔐 Secure by default
🧩 Easy to integrate
🏗️ Infrastructure-as-Code friendly

---

## 📦 How to get it

### Step 1 — Clone the repository

```
git clone https://github.com/your-repo/serverless-infra-health-scanner.git
cd serverless-infra-health-scanner
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

## ⚙️ What gets created automatically

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

**Example**

```
payments-connect
payments-connect-db-secret
payments-alb
```

---

### Step 2 — Store database credentials in Secrets Manager

**Required secret structure**

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
module "infra_health_scanner" {
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
* Provide early-warning signals for platform instability

---

## 💰 Cost & Observability Philosophy

This scanner is intentionally designed as a **lightweight health monitoring layer**, not a full observability platform.

Traditional monitoring systems continuously collect large volumes of telemetry, which provides deep visibility but can increase operational cost and complexity at scale.

This system takes a different approach:

* Runs **targeted diagnostic checks** on a schedule
* Collects **only actionable health signals**
* Publishes alerts when instability patterns appear
* Avoids continuous high-volume telemetry collection

**The result**

💸 Lower monitoring overhead
⚡ Faster detection of common reliability risks
🧠 Simpler operational model
📉 Cost-conscious infrastructure monitoring

---

## 📊 Example Cost Comparison

The following example illustrates a **typical small-to-medium production environment**.

### Assumptions

* 1 Kubernetes cluster (~10 nodes)
* 1 PostgreSQL database
* Standard CloudWatch retention
* Health scanner runs every 5 minutes
* Moderate log and metric volume

| Monitoring Approach       | Components                      | Estimated Monthly Cost | Monitoring Model        | Maintenance Effort          |
| ------------------------- | ------------------------------- | ---------------------- | ----------------------- | --------------------------- |
| Container + DB Insights   | Continuous telemetry collection | ₹8,000 – ₹20,000       | Always-on monitoring    | Low (fully managed)         |
| Serverless Health Scanner | Scheduled diagnostic checks     | ₹100 – ₹800            | Event-driven monitoring | Low–Moderate (custom logic) |

---

### What this comparison shows

This scanner reduces monitoring overhead by:

* Running **periodic targeted diagnostics** instead of continuous telemetry
* Publishing alerts only when instability patterns appear
* Minimizing metric and log ingestion volume

---

### Important Note

Actual costs depend on:

* Resource count
* Metric and log volume
* Retention duration
* Monitoring frequency
* Regional pricing

This comparison is intended to illustrate **architectural tradeoffs**, not provide exact pricing.

---

## 🧠 Why this exists

Most monitoring systems react **after failure**.

This scanner focuses on detecting **early instability signals**, enabling teams to respond before incidents escalate into outages.

It reflects a simple production principle:

**Small, automated health checks prevent large incidents.**

---

## 🏭 Production Characteristics

✅ Serverless and event-driven
✅ Secure credential handling via Secrets Manager
✅ Infrastructure-as-Code deployment
✅ Minimal operational overhead
✅ Cloud-native reliability design
✅ Platform-friendly integration
✅ Cost-aware monitoring architecture

---

## 🚀 Repository Purpose

This project demonstrates practical **Platform Engineering** and **Reliability Engineering** patterns:

* Event-driven infrastructure automation
* Proactive system health monitoring
* Cost-aware operational design
* Production-ready serverless architecture
* Infrastructure observability integration
* FinOps-aligned reliability tooling

---

## 📌 Status

**Production-ready reference implementation**
Designed for real infrastructure environments and platform teams.

## 📄 License

Licensed under the Apache License 2.0.