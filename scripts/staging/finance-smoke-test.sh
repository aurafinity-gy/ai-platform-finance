#!/bin/sh
set -eu

tenant_id='10000000-0000-0000-0000-000000000001'
email='operator.staging@example.test'
work="$(mktemp -d /run/finance-smoke.XXXXXX)"
trap 'rm -rf "$work"' EXIT

for required in \
  /run/m5-provider-admission/password \
  /srv/platform/runtime-secrets/supabase-anon-key; do
  test -s "$required"
done
echo 'stage=inputs.pass'

auth_ip="$(docker inspect ai-platform-foundation-auth-1 \
  --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}')"
finance_ip="$(docker inspect ai-platform-finance-finance-api-1 \
  --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}')"
test -n "$auth_ip"
test -n "$finance_ip"

anon_key="$(tr -d '\r\n' < /srv/platform/runtime-secrets/supabase-anon-key)"
python3 - "$email" /run/m5-provider-admission/password "$work/auth.json" <<'PY'
import json
import sys

json.dump(
    {"email": sys.argv[1], "password": open(sys.argv[2]).read().strip()},
    open(sys.argv[3], "w"),
)
PY

auth_http="$(curl --silent --show-error \
  --output "$work/auth-response.json" \
  --write-out '%{http_code}' \
  --request POST \
  --header "apikey: $anon_key" \
  --header 'Content-Type: application/json' \
  --data-binary "@$work/auth.json" \
  "http://${auth_ip}:9999/token?grant_type=password")"
test "$auth_http" = 200
test -s "$work/auth-response.json"
access_token="$(python3 - "$work/auth-response.json" <<'PY'
import json
import sys

print(json.load(open(sys.argv[1]))["access_token"])
PY
)"
test -n "$access_token"
echo 'stage=auth.pass'

request_id="$(cat /proc/sys/kernel/random/uuid)"
idempotency_key="finance-smoke-$(date -u +%Y%m%d%H%M%S)"
correlation_id="finance-smoke-$(date -u +%Y%m%d%H%M%S)"
python3 - "$request_id" "$work/request.json" <<'PY'
import json
import sys

json.dump(
    {
        "contract_version": 1,
        "request_id": sys.argv[1],
        "source_domain": "finance",
        "source_reference": "staging-smoke-test",
        "instrument": "AAPL",
        "objective": "Validate asynchronous Finance staging behavior.",
        "domain_context": {"as_of": "staging"},
    },
    open(sys.argv[2], "w"),
)
PY

enqueue() {
  curl --silent --show-error \
    --output "$1" \
    --write-out '%{http_code}' \
    --request POST \
    --header "Authorization: Bearer $access_token" \
    --header "X-Tenant-ID: $tenant_id" \
    --header "X-Correlation-ID: $correlation_id" \
    --header "Idempotency-Key: $idempotency_key" \
    --header 'Content-Type: application/json' \
    --data-binary "@$work/request.json" \
    "http://${finance_ip}:8011/v1/finance-researches/jobs"
}

first_http="$(enqueue "$work/first.json")"
echo "stage=enqueue http=$first_http"
test "$first_http" = 202
job_id="$(python3 - "$work/first.json" <<'PY'
import json
import sys

print(json.load(open(sys.argv[1]))["job_id"])
PY
)"
test -n "$job_id"
echo 'stage=enqueue.pass http=202'

docker restart ai-platform-finance-finance-worker-1 >/dev/null
echo 'stage=worker-restarted'

final_status=''
for _ in $(seq 1 30); do
  status_http="$(curl --silent --show-error \
    --output "$work/status.json" \
    --write-out '%{http_code}' \
    --header "Authorization: Bearer $access_token" \
    --header "X-Tenant-ID: $tenant_id" \
    --header "X-Correlation-ID: $correlation_id" \
    "http://${finance_ip}:8011/v1/finance-researches/jobs/${job_id}")"
  test "$status_http" = 200
  final_status="$(python3 - "$work/status.json" <<'PY'
import json
import sys

print(json.load(open(sys.argv[1]))["status"])
PY
)"
  case "$final_status" in
    succeeded) break ;;
    failed) echo 'stage=async.failed' >&2; exit 1 ;;
  esac
  sleep 1
done
test "$final_status" = succeeded
echo 'stage=worker-recovery.pass status=succeeded'

replay_http="$(enqueue "$work/replay.json")"
echo "stage=replay http=$replay_http"
test "$replay_http" = 202
replay_job_id="$(python3 - "$work/replay.json" <<'PY'
import json
import sys

print(json.load(open(sys.argv[1]))["job_id"])
PY
)"
test "$replay_job_id" = "$job_id"
echo 'stage=idempotency.pass same_job_id=true'

unauthenticated_http="$(curl --silent --show-error \
  --output /dev/null \
  --write-out '%{http_code}' \
  "http://${finance_ip}:8011/v1/finance-researches/jobs/${job_id}")"
echo "stage=unauthenticated-rejection http=$unauthenticated_http"
test "$unauthenticated_http" = 401
echo 'stage=unauthenticated-rejection.pass http=401'

audit_count="$(docker exec ai-platform-foundation-database-1 \
  psql -U supabase_admin -d postgres -Atc \
  "select count(*) from platform.audit_entries where tenant_id = '${tenant_id}' and action = 'finance.research.created';")"
test "$audit_count" -ge 1
echo "stage=audit.pass entries=$audit_count"

echo '{"event":"finance_staging_smoke.pass","async_status":"succeeded","idempotency":"same_job_id","worker_restart":"recovered","unauthenticated_status":401}'
