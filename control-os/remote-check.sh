set -e
printf "== releases ==\n"
ls -ldt /opt/control-os/releases/*/ | head -5
printf "== current ==\n"
readlink /opt/control-os/current
printf "== latest listing ==\n"
latest=$(ls -1dt /opt/control-os/releases/*/ | head -1)
echo LATEST=$latest
ls -la "$latest" | sed -n '1,20p'
printf "== artifact dirs ==\n"
test -d "$latest/node_modules" && echo NODE_MODULES_PRESENT || echo NODE_MODULES_MISSING
test -d "$latest/dist" && echo DIST_PRESENT || echo DIST_MISSING
printf "== temp archive dir ==\n"
ls -ld /tmp/control-os-release-24625975437-1 2>/dev/null || echo REMOTE_ARCHIVE_DIR_MISSING
printf "== services ==\n"
systemctl is-active nginx
systemctl is-active control-os.target 2>/dev/null || true
systemctl is-active control-os-root-app-api 2>/dev/null || true