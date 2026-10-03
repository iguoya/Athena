#!/bin/bash
# One-shot: stop driver, flutter clean, reopen via launcher.
set -euo pipefail
REPO="/Users/tiger/Athena"
LOG="/Users/tiger/Library/Logs/Athena/driver-restart.log"
mkdir -p "$(dirname "$LOG")"
exec > >(tee "$LOG") 2>&1

echo "===== $(date) restart clean driver ====="
cd "$REPO"

"$REPO/launcher/target/debug/launcher" stop driver || true
killall -9 athena-driver 2>/dev/null || true
pkill -9 -f '/Users/tiger/Athena/subjects/driver' 2>/dev/null || true
sleep 2

export DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer
export PATH="/Applications/Xcode.app/Contents/Developer/usr/bin:$PATH"

cd "$REPO/subjects/driver"
flutter clean
echo CLEAN_OK

cd "$REPO"
"$REPO/launcher/target/debug/launcher" open driver
echo OPEN_ISSUED

# Wait until ready / running with a fresh build
for i in $(seq 1 120); do
  state=$("$REPO/launcher/target/debug/launcher" list 2>/dev/null | awk '/^driver\t/{print $NF}')
  echo "$(date +%H:%M:%S) state=$state"
  if [ "$state" = "运行中" ] || [ "$state" = "ready" ]; then
    # Confirm log shows a new launch after CLEAN
    if grep -q 'CLEAN_OK' "$LOG" && tail -5 /Users/tiger/Library/Logs/Athena/driver.log | grep -q 'Built\|Launching\|Syncing'; then
      echo READY
      "$REPO/launcher/target/debug/launcher" list | grep driver
      exit 0
    fi
  fi
  sleep 3
done
echo TIMEOUT
tail -40 /Users/tiger/Library/Logs/Athena/driver.log
exit 1
