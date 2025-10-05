import os
import re
import shlex
import subprocess
import time
from collections.abc import Iterable

from minitap.mobile_use.utils.logger import get_logger

logger = get_logger(__name__)

# Environment controls
ENV_ENABLED = os.getenv("ADB_AUTO_TCP_ENABLED", "1") == "1"
ENV_CONNECT_ADDR = os.getenv("ADB_CONNECT_ADDR", "").strip()
ENV_TCP_PORT = int(os.getenv("ADB_TCP_PORT", "5555") or 5555)
ENV_MAX_RETRIES = int(os.getenv("ADB_CONNECT_MAX_RETRIES", "5") or 5)
ENV_BACKOFF_START = float(os.getenv("ADB_CONNECT_BACKOFF_START", "1.0") or 1.0)
ENV_BACKOFF_FACTOR = float(os.getenv("ADB_CONNECT_BACKOFF_FACTOR", "1.7") or 1.7)
ENV_PREFERRED_METHODS = [m.strip() for m in os.getenv("ADB_PREFERRED_METHODS", "env,mdns,usb_tcpip,pairing").split(",")]

# Pairing: Android 11+
ENV_PAIR_HOST_PORT = os.getenv("ADB_PAIR_HOST_PORT", "").strip()  # e.g. "192.168.1.50:37099"
ENV_PAIR_CODE = os.getenv("ADB_PAIR_CODE", "").strip()  # 6-digit code from device


class ADBError(Exception):
    pass


def _run(cmd: str, timeout: int = 30, check: bool = False) -> tuple[int, str, str]:
    logger.debug(f"$ {cmd}")
    proc = subprocess.run(
        shlex.split(cmd),
        capture_output=True,
        timeout=timeout,
        text=True,
    )
    out = proc.stdout.strip()
    err = proc.stderr.strip()
    if check and proc.returncode != 0:
        raise ADBError(f"Command failed ({proc.returncode}): {cmd}\nSTDOUT: {out}\nSTDERR: {err}")
    return proc.returncode, out, err


def _devices() -> list[str]:
    rc, out, _ = _run("adb devices -l")
    if rc != 0:
        return []
    lines = [ln.strip() for ln in out.splitlines() if ln.strip()]
    devs: list[str] = []
    for ln in lines[1:]:  # skip header
        parts = ln.split()
        if len(parts) >= 2 and parts[1] == "device":
            devs.append(parts[0])
    return devs


def _mdns_services() -> list[tuple[str, int]]:
    """Return list of (host, port) from `adb mdns services` for connectable services."""
    rc, out, _ = _run("adb mdns services")
    if rc != 0:
        return []
    hosts: list[tuple[str, int]] = []
    for ln in out.splitlines():
        # Example: adb-tls-connect _adb-tls-connect._tcp. local. 192.168.1.50:41857
        if "adb-tls-connect" in ln or "_adb._tcp" in ln:
            m = re.search(r"(\d+\.\d+\.\d+\.\d+):(\d+)", ln)
            if m:
                hosts.append((m.group(1), int(m.group(2))))
    return hosts


def _get_device_ip_via_shell() -> str | None:
    """Try to infer device WLAN IP while USB-connected."""
    # Try common commands
    for cmd in (
        "adb shell ip route",
        "adb shell ip addr show wlan0",
        "adb shell getprop dhcp.wlan0.ipaddress",
    ):
        rc, out, _ = _run(cmd)
        if rc != 0 or not out:
            continue
        # ip route example: default via 192.168.1.1 dev wlan0  proto dhcp  src 192.168.1.50
        m = re.search(r"\bsrc\s+(\d+\.\d+\.\d+\.\d+)", out)
        if m:
            return m.group(1)
        m2 = re.search(r"(\d+\.\d+\.\d+\.\d+)", out)
        if m2:
            return m2.group(1)
    return None


def _sleep_backoff(attempt: int):
    delay = ENV_BACKOFF_START * (ENV_BACKOFF_FACTOR ** max(0, attempt - 1))
    delay = min(delay, 30.0)
    logger.info(f"Retrying in {delay:.1f}s...")
    time.sleep(delay)


def _connect_targets(targets: Iterable[tuple[str, int]]) -> str | None:
    for host, port in targets:
        addr = f"{host}:{port}"
        logger.info(f"Attempting: adb connect {addr}")
        rc, out, err = _run(f"adb connect {addr}")
        if rc == 0 and ("connected" in out.lower() or "already connected" in out.lower()):
            logger.success(f"Connected to {addr}")
            return addr
        logger.warning(f"Connect failed to {addr}: {out or err}")
    return None


def try_env_connect() -> str | None:
    if not ENV_CONNECT_ADDR:
        return None
    # allow comma-separated list
    addrs = [a.strip() for a in ENV_CONNECT_ADDR.split(",") if a.strip()]
    targets = []
    for a in addrs:
        if ":" in a:
            host, port_s = a.rsplit(":", 1)
            try:
                port = int(port_s)
            except ValueError:
                port = ENV_TCP_PORT
        else:
            host, port = a, ENV_TCP_PORT
        targets.append((host, port))
    return _connect_targets(targets)


def try_mdns_connect() -> str | None:
    hosts = _mdns_services()
    if not hosts:
        logger.info("No mDNS adb-tls-connect services discovered")
        return None
    return _connect_targets(hosts)


def try_usb_tcpip_then_connect() -> str | None:
    # Check if any USB device is present
    devs = _devices()
    if not devs:
        logger.info("No USB devices detected for tcpip enabling")
        return None
    # Enable tcpip on the first device
    rc, out, err = _run(f"adb -s {devs[0]} tcpip {ENV_TCP_PORT}")
    if rc != 0:
        logger.warning(f"adb tcpip failed: {out or err}")
        return None
    # Find device WLAN IP and connect
    ip = _get_device_ip_via_shell()
    if not ip:
        logger.warning("Could not determine device IP over USB")
        return None
    return _connect_targets([(ip, ENV_TCP_PORT)])


def try_pairing_then_connect() -> str | None:
    """Wireless debugging pairing flow (Android 11+).
    Requires user-provided ADB_PAIR_HOST_PORT and ADB_PAIR_CODE from device.
    """
    if not ENV_PAIR_HOST_PORT or not ENV_PAIR_CODE:
        logger.info("Pairing info not provided (ADB_PAIR_HOST_PORT/ADB_PAIR_CODE)")
        return None
    # adb pair host:port code
    rc, out, err = _run(f"adb pair {ENV_PAIR_HOST_PORT} {ENV_PAIR_CODE}")
    if rc != 0:
        logger.warning(f"adb pair failed: {out or err}")
        return None
    # After pairing, device typically advertises adb-tls-connect via mDNS
    # try mdns first, then env connect as fallback
    return try_mdns_connect() or try_env_connect()


def attempt_auto_connect() -> str | None:
    """Try to establish ADB TCP/IP connection using multiple non-root methods.

    Returns the connected address (host:port) on success, or None if all methods failed.
    """
    if not ENV_ENABLED:
        logger.info("ADB auto TCP is disabled (ADB_AUTO_TCP_ENABLED!=1)")
        return None

    methods = []
    for m in ENV_PREFERRED_METHODS:
        m = m.lower()
        if m == "env":
            methods.append(("env", try_env_connect))
        elif m == "mdns":
            methods.append(("mdns", try_mdns_connect))
        elif m == "usb_tcpip":
            methods.append(("usb_tcpip", try_usb_tcpip_then_connect))
        elif m == "pairing":
            methods.append(("pairing", try_pairing_then_connect))

    for attempt in range(1, ENV_MAX_RETRIES + 1):
        for name, fn in methods:
            try:
                logger.info(f"[ADB-AUTO] Method: {name} (attempt {attempt}/{ENV_MAX_RETRIES})")
                addr = fn()
                if addr:
                    logger.success(f"[ADB-AUTO] Connected using method '{name}' → {addr}")
                    return addr
            except Exception as e:
                logger.warning(f"[ADB-AUTO] Method '{name}' error: {e}")
        if attempt < ENV_MAX_RETRIES:
            _sleep_backoff(attempt)

    logger.error("[ADB-AUTO] All ADB TCP methods failed. See logs for details.")
    return None

