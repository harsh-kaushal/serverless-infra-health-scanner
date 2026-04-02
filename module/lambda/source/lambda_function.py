import os
import json
import boto3
import pg8000.native as pg
import concurrent.futures
from datetime import datetime

import requests
import re
from botocore.exceptions import ClientError

# To suppress TLS warning from self-signed alb cert
import warnings
from urllib3.exceptions import InsecureRequestWarning
warnings.simplefilter("ignore", InsecureRequestWarning)

rds = boto3.client("rds")
secrets_client = boto3.client("secretsmanager")
cloudwatch = boto3.client("cloudwatch")

elbv2 = boto3.client("elbv2")

DB_SUFFIX = os.environ.get("DB_SUFFIX", "-testing")
SECRET_SUFFIX = os.environ.get("SECRET_SUFFIX", "-testing-db-secret")
MAX_THREADS = int(os.environ.get("MAX_THREADS", "10"))

ALB_SUFFIX = os.environ.get("ALB_SUFFIX", "-alb")
PROMETHEUS_PATH = os.environ.get("PROMETHEUS_PATH", "/prometheus/api/v1/query")

# Queries stuck from last 90 mins AND containers restarts in last 90 mins
THRESHOLD_MINUTES = int(os.environ.get("THRESHOLD_MINUTES", "90"))

def log(msg, **kwargs):
  print(json.dumps({"message": msg, "time": datetime.utcnow().isoformat(), **kwargs}))

# ---------------------------------------------------------
# Discover DBs from RDS (only identifier + engine used)
# ---------------------------------------------------------
def discover_databases():
  instances = rds.describe_db_instances()["DBInstances"]
  
  filtered = [
    {
      "identifier": db["DBInstanceIdentifier"],
      "engine": db["Engine"]
    }
    for db in instances
    if db["DBInstanceIdentifier"].endswith(DB_SUFFIX)
  ]
  
  log("Discovered databases", count=len(filtered))
  return filtered

def discover_albs(prefixes):
  """
  prefixes: list of env/base prefixes (derived from DB identifiers)
  """
  try:
    lbs = elbv2.describe_load_balancers()["LoadBalancers"]
  except ClientError as e:
    log("Failed to list ALBs", error=str(e))
    return []

  matched = []
  for lb in lbs:
    name = lb["LoadBalancerName"]
    for p in prefixes:
      if name == f"{p}{ALB_SUFFIX}":
        matched.append({
          "name": name,
          "dns": lb["DNSName"]
        })
  
  log("Discovered ALBs", count=len(matched))
  return matched

# ---------------------------------------------------------
# Resolve Secrets: dbname-testing -> dbname-testing-db-secret
# ---------------------------------------------------------
def fetch_db_credentials(db_identifier):
  # Remove DB_SUFFIX and append SECRET_SUFFIX
  if db_identifier.endswith(DB_SUFFIX):
    base = db_identifier[:-len(DB_SUFFIX)]
  else:
    base = db_identifier
  
  secret_name = f"{base}{SECRET_SUFFIX}"
  
  try:
    secret_value = secrets_client.get_secret_value(SecretId=secret_name)
    creds = json.loads(secret_value["SecretString"])
    log("Secret loaded", secret=secret_name)
    return creds
  except secrets_client.exceptions.ResourceNotFoundException:
    log("Secret not found", secret=secret_name)
    return None

# ---------------------------------------------------------
# Connect using pg8000 with secret formatting
# ---------------------------------------------------------
def scan_postgres(db_identifier, creds):
  try:
    conn = pg.Connection(
      user=creds["username"],
      password=creds["rds_password"],
      host=creds["host"], # override host from secret
      port=creds.get("port", 5432), # optional, default postgres port
      database=creds["dbname"],
      timeout=5
    )
  except Exception as e:
    log("DB connection failed", db=db_identifier, error=str(e))
    return {"db": db_identifier, "error": str(e), "stuck": []}

  query = f"""
  SELECT
    pid,
    usename,
    application_name,
    now() - query_start AS duration,
    wait_event_type,
    wait_event,
    query
  FROM pg_stat_activity
  WHERE state = 'active'
    AND now() - query_start > interval '{THRESHOLD_MINUTES} minutes'
  ORDER BY duration DESC;
  """
  
  try:
    rows = conn.run(query)
  except Exception as e:
    log("Query execution failed", db=db_identifier, error=str(e))
    return {"db": db_identifier, "error": str(e), "stuck": []}
  finally:
    conn.close()

  formatted = [
    {
      "pid": r[0],
      "user": r[1],
      "application": r[2],
      "duration": str(r[3]),
      "wait_type": r[4],
      "wait_event": r[5],
      "query": r[6],
    }
    for r in rows
  ]

  return {"db": db_identifier, "error": None, "stuck": formatted}

def fetch_prometheus_restart_increase(alb):
  url = f"https://{alb['dns']}{PROMETHEUS_PATH}"
  
  try:
    query = "round(sum(increase(kube_pod_container_status_restarts_total[{0}m])))".format(THRESHOLD_MINUTES)
    
    resp = requests.get(
      url,
      params={"query": query},
      timeout=5,
      verify=False # self-signed cert
    )
    resp.raise_for_status()
    data = resp.json()

    if data["status"] != "success":
      raise ValueError("Prometheus query failed")
    
    result = data["data"]["result"]
    
    if not result:
      return 0
      
    # result[0]["value"] => [timestamp, "number"]
    return int(round(float(result[0]["value"][1])))

  except Exception as e:
    log("Prometheus query failed", alb=alb["name"], error=str(e))
    return 0

# ---------------------------------------------------------
# Publish CloudWatch
# ---------------------------------------------------------
def publish_metric(db_identifier, count):
  # This function was collapsed in the screenshot, but follows the pattern below:
  cloudwatch.put_metric_data(
    Namespace="CustomInsights",
    MetricData=[
      {
        "MetricName": "StuckQueries",
        "Dimensions": [{"Name": "DBIdentifier", "Value": db_identifier}],
        "Value": count
      }
    ]
  )

def publish_alb_metric(alb_name, count):
  cloudwatch.put_metric_data(
    Namespace="CustomInsights",
    MetricData=[
      {
        "MetricName": "ContainerRestarts",
        "Dimensions": [
          {"Name": "ALBName", "Value": alb_name}
        ],
        "Value": count
      }
    ]
  )
  log("Metric published", alb=alb_name, restarts_count=count)

# ---------------------------------------------------------
# Worker (each DB in parallel)
# ---------------------------------------------------------
def scan_single_database(db):
  db_identifier = db["identifier"]

  creds = fetch_db_credentials(db_identifier)
  if not creds:
    return {"db": db_identifier, "error": "secret-missing", "stuck": []}

  if "postgres" not in creds["engine"]:
    log("Skipping non-progress DB", db=db_identifier, engine=creds["engine"])
    return {"db": db_identifier, "error": "unsupported-engine", "stuck":[]}

  result = scan_postgres(db_identifier, creds)

  publish_metric(db_identifier, len(result["stuck"]))

  log("Scan complete", db=db_identifier, stuck=len(result["stuck"]))

  return result

def scan_single_alb(alb):
  restarts = fetch_prometheus_restart_increase(alb)
  publish_alb_metric(alb["name"], restarts)
  
  log("ALB scan complete", alb=alb["name"], restarts=restarts)
  
  return {
    "alb": alb["name"],
    "restarts": restarts
  }

# ---------------------------------------------------------
# Lambda Handler
# ---------------------------------------------------------
def lambda_handler(event, context):
  log("Lambda started", suffix=DB_SUFFIX, secret_suffix=SECRET_SUFFIX)
  
  dbs = discover_databases()
  if not dbs:
    return {"status": "no-dbs"}
  
  results = []
  
  with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
    futures = [executor.submit(scan_single_database, db) for db in dbs]
    for f in concurrent.futures.as_completed(futures):
      results.append(f.result())

  # ---------
  # NEW: ALB SCANNING
  # ---------
  prefixes = [
    db["identifier"][:-len(DB_SUFFIX)]
    for db in dbs
    if db["identifier"].endswith(DB_SUFFIX)
  ]
  
  albs = discover_albs(prefixes)
  
  alb_results = []
  with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
    futures = [executor.submit(scan_single_alb, alb) for alb in albs]
    for f in concurrent.futures.as_completed(futures):
      alb_results.append(f.result())
      
  log("Lambda finished", DBs=len(results), ALBs=len(alb_results))
  
  return {
    "status": "ok",
    "databases": results,
    "albs": alb_results
  }
