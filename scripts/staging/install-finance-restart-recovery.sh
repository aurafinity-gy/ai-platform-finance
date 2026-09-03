#!/bin/sh
set -eu

script_directory="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
tools_directory="${FINANCE_TOOLS_DIRECTORY:-/srv/platform/finance/tools}"
hooks_directory='/srv/platform/hooks'
bootstrap_path="${tools_directory}/bootstrap-finance-staging-permissions.sh"
hook_path="${hooks_directory}/post-start-reconcile"

install -d -o root -g root -m 0700 "$tools_directory"
install -d -o root -g root -m 0700 "$hooks_directory"
install -o root -g root -m 0700 \
  "${script_directory}/bootstrap-finance-staging-permissions.sh" \
  "$bootstrap_path"

cat > "$hook_path" <<EOF
#!/bin/sh
set -eu
exec "$bootstrap_path"
EOF
chown root:root "$hook_path"
chmod 0700 "$hook_path"

systemctl daemon-reload
systemctl enable platform-post-start-reconcile.service
systemctl restart platform-post-start-reconcile.service

echo 'finance_restart_recovery.installed'
