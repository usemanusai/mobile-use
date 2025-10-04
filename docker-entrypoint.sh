#!/bin/bash

set -eu


# Allow running without a connected device (for GUI-only workflows)
if [[ "${ALLOW_NO_DEVICE:-}" = "1" ]] || [[ -z "${ADB_CONNECT_ADDR:-}" ]]; then
    echo "Starting without waiting for device (ALLOW_NO_DEVICE=${ALLOW_NO_DEVICE:-0}, ADB_CONNECT_ADDR='${ADB_CONNECT_ADDR:-}')"
    exec mobile-use "$@"
fi

while true; do
    set +e
    adb connect "$ADB_CONNECT_ADDR"
    state="$(adb get-state 2>/dev/null)"
    set -e

    adb devices

    if [[ "$state" = "device" ]]; then
        echo "Device is connected and authorized!"
        break
    fi

    set +e; adb disconnect "$ADB_CONNECT_ADDR"; set -e

    echo "Waiting for device authorization... (accept the prompt on your phone)"
    sleep 2
done

mobile-use "$@"
