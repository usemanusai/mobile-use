# Wireless ADB (ADB over TCP/IP) – Non‑root Methods and Auto‑Connect

This guide explains how Mobile‑Use can connect to Android devices over Wi‑Fi without root, and how to enable its automatic connection feature.

## Supported non‑root methods

1) Manual env address (no pairing required)
- If you already know the device address, set `ADB_CONNECT_ADDR` (e.g. `192.168.1.50:5555`) and Mobile‑Use will try `adb connect` to it.

2) mDNS discovery (Android 11+ wireless debugging, previously paired)
- On Android 11+, Wireless debugging advertises services via mDNS. If your host has been paired before, Mobile‑Use can discover and connect.
- Uses `adb mdns services` then `adb connect <ip:port>`.

3) USB‑initiated TCP/IP (classic)
- Connect the device via USB once, ensure USB debugging is allowed.
- Mobile‑Use runs: `adb tcpip 5555` on the device and tries to find the device's WLAN IP via `adb shell` to connect: `adb connect <device_ip>:5555`.
- Works on most devices and does not require root.

4) Wireless debugging pairing (Android 11+)
- In Developer options → Wireless debugging → Pair device with pairing code, the device shows `host:port` and a 6‑digit code.
- Provide these via `ADB_PAIR_HOST_PORT` and `ADB_PAIR_CODE`. Mobile‑Use runs `adb pair`, then tries mDNS/ENV connect.
- This flow requires manual action on the device to display a pairing code; after pairing once, future connects are typically automatic via mDNS.

## Enable auto‑connect

Set the following (compose already passes them through if present in `.env`):

- `ADB_AUTO_TCP_ENABLED=1` (default) – turn the feature on/off
- `ADB_PREFERRED_METHODS=env,mdns,usb_tcpip,pairing` – order of attempts
- `ADB_TCP_PORT=5555` – port for classic TCP/IP mode
- `ADB_CONNECT_ADDR=` – optional address list (comma‑separated) for direct connects
- `ADB_PAIR_HOST_PORT=` – host:port from device pairing UI (Android 11+)
- `ADB_PAIR_CODE=` – 6‑digit pairing code from device UI
- Timeouts/retries/backoff:
  - `ADB_CONNECT_MAX_RETRIES=5`
  - `ADB_CONNECT_BACKOFF_START=1.0`
  - `ADB_CONNECT_BACKOFF_FACTOR=1.7`

## Docker compose

`docker-compose.yml` includes these environment variables so you can control the behavior via `.env`.

For example, in your `.env`:

```
ADB_AUTO_TCP_ENABLED=1
ADB_PREFERRED_METHODS=env,mdns,usb_tcpip,pairing
ADB_TCP_PORT=5555
# ADB_CONNECT_ADDR=192.168.1.50:5555
# For Android 11+ pairing (optional, only when pairing UI is open on the device):
# ADB_PAIR_HOST_PORT=192.168.1.50:39191
# ADB_PAIR_CODE=123456
```

## How it integrates with Mobile‑Use

- If `ALLOW_NO_DEVICE=1`, the Web GUI can start without a device.
- When you submit a task and the agent needs a device, Mobile‑Use will run the auto‑connect flow before failing.
- On success, the agent proceeds with the task; otherwise it returns a clear error.

## Prerequisites

- Developer options enabled on the device
- USB debugging allowed (for USB‑initiated method)
- Wireless debugging enabled (for Android 11+ pairing/mDNS)
- Host and device on the same Wi‑Fi network

## Troubleshooting

- `device offline`: run `adb kill-server`, then retry; verify USB debugging authorization prompt on the device.
- `failed to connect`: verify device and host are on same network; try `adb mdns services` to see advertised endpoints.
- `pairing failed`: ensure the pairing code is still valid and matches `ADB_PAIR_HOST_PORT` from the device UI.
- Firewalls: allow local network/ports used by adb (dynamic for wireless debugging) and 5555 for classic TCP/IP.

## Notes

- Root is not required for any of the above methods.
- Wireless debugging pairing requires manual interaction once. After pairing, reconnection is usually seamless via mDNS.

