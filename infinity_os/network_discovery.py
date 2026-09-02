from __future__ import annotations

import ipaddress
import json
import os
import re
import socket
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import psutil
except Exception:  # optional at import time
    psutil = None

from .contracts import ToolResult


class NetworkDiscovery:
    """Local-only device discovery for Infinity OS.

    This deliberately limits active discovery to private IPv4 networks that
    the current computer is already connected to. It does not scan ports,
    test credentials, fingerprint services, or probe public Internet ranges.
    """

    _VIRTUAL_HINTS = (
        "loopback", "docker", "wsl", "vmware", "virtualbox", "vbox",
        "hyper-v", "vethernet", "tailscale", "zerotier"
    )

    def __init__(self, security=None):
        self.security = security
        self.last_lan = []
        self.last_bluetooth = []

    @staticmethod
    def _is_private_host(value: str) -> bool:
        try:
            ip = ipaddress.ip_address(value)
            return bool(ip.version == 4 and ip.is_private and not ip.is_loopback and not ip.is_multicast and not ip.is_unspecified)
        except Exception:
            return False

    @staticmethod
    def _safe_network(ip_text: str, mask_text: str):
        try:
            ip = ipaddress.IPv4Address(ip_text)
            net = ipaddress.IPv4Network(f"{ip_text}/{mask_text}", strict=False)
            if not ip.is_private or ip.is_loopback or ip.is_link_local:
                return None
            if net.prefixlen < 24:
                net = ipaddress.IPv4Network(f"{ip_text}/24", strict=False)
            if net.prefixlen > 30:
                return None
            return net
        except Exception:
            return None

    def local_networks(self):
        rows = []
        if psutil is None:
            return rows
        stats = psutil.net_if_stats()
        for iface, addrs in psutil.net_if_addrs().items():
            if iface in stats and not stats[iface].isup:
                continue
            low = iface.lower()
            if any(h in low for h in self._VIRTUAL_HINTS):
                continue
            for addr in addrs:
                if getattr(addr, "family", None) != socket.AF_INET:
                    continue
                net = self._safe_network(addr.address, addr.netmask or "255.255.255.0")
                if not net:
                    continue
                rows.append({"interface": iface, "ip": addr.address, "network": str(net), "_network": net})
        out, seen = [], set()
        for row in rows:
            if row["network"] in seen:
                continue
            seen.add(row["network"])
            out.append(row)
        return out[:2]

    @staticmethod
    def _run(command, timeout=8):
        kwargs = dict(capture_output=True, text=True, timeout=timeout)
        if os.name == "nt":
            kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        return subprocess.run(command, **kwargs)

    @staticmethod
    def _normalize_mac(value: str) -> str:
        value = (value or "").strip().replace("-", ":").upper()
        if re.fullmatch(r"(?:[0-9A-F]{2}:){5}[0-9A-F]{2}", value):
            return value
        return ""

    def _windows_neighbors(self):
        rows = []
        if os.name != "nt":
            return rows
        ps = (
            "Get-NetNeighbor -AddressFamily IPv4 -ErrorAction SilentlyContinue | "
            "Where-Object {$_.State -ne 'Unreachable'} | "
            "Select-Object IPAddress,LinkLayerAddress,State,InterfaceAlias | ConvertTo-Json -Compress"
        )
        try:
            p = self._run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps], timeout=10)
            if p.returncode == 0 and p.stdout.strip():
                data = json.loads(p.stdout)
                if isinstance(data, dict):
                    data = [data]
                for item in data or []:
                    ip = str(item.get("IPAddress") or "")
                    if not self._is_private_host(ip):
                        continue
                    rows.append({
                        "type": "LAN",
                        "name": ip,
                        "ip": ip,
                        "mac": self._normalize_mac(str(item.get("LinkLayerAddress") or "")),
                        "interface": str(item.get("InterfaceAlias") or ""),
                        "state": str(item.get("State") or "Known"),
                        "source": "Windows neighbor table",
                    })
                return rows
        except Exception:
            pass
        return self._arp_neighbors()

    def _arp_neighbors(self):
        rows = []
        try:
            p = self._run(["arp", "-a"], timeout=8)
        except Exception:
            return rows
        current_iface = ""
        for line in (p.stdout or "").splitlines():
            m_iface = re.search(r"Interface:\s+([0-9.]+)", line, re.I)
            if m_iface:
                current_iface = m_iface.group(1)
                continue
            m = re.search(r"\b(\d{1,3}(?:\.\d{1,3}){3})\s+([0-9a-fA-F:-]{17})\s+(\w+)", line)
            if not m:
                continue
            ip = m.group(1)
            if not self._is_private_host(ip):
                continue
            rows.append({
                "type": "LAN", "name": ip, "ip": ip,
                "mac": self._normalize_mac(m.group(2)),
                "interface": current_iface, "state": m.group(3), "source": "ARP cache"
            })
        return rows

    @staticmethod
    def _in_allowed_networks(ip_text, networks):
        try:
            ip = ipaddress.IPv4Address(ip_text)
            return any(ip in row["_network"] for row in networks)
        except Exception:
            return False

    def _ping(self, ip_text: str, timeout_ms=260):
        try:
            if os.name == "nt":
                p = self._run(["ping", "-n", "1", "-w", str(int(timeout_ms)), ip_text], timeout=max(2, timeout_ms / 1000 + 1.5))
            else:
                p = self._run(["ping", "-c", "1", "-W", "1", ip_text], timeout=2)
            return p.returncode == 0
        except Exception:
            return False

    def discover_lan(self, active=True):
        networks = self.local_networks()
        if not networks:
            return ToolResult(False, "No active private IPv4 network was found.", {"devices": [], "networks": []})

        before = self._windows_neighbors()
        live_ips = {d["ip"] for d in before if self._in_allowed_networks(d["ip"], networks)}

        if active:
            targets = []
            local_ips = {row["ip"] for row in networks}
            for row in networks:
                for host in row["_network"].hosts():
                    text = str(host)
                    if text not in local_ips:
                        targets.append(text)
            targets = targets[:254]
            with ThreadPoolExecutor(max_workers=min(36, max(1, len(targets)))) as pool:
                jobs = {pool.submit(self._ping, ip): ip for ip in targets}
                for job in as_completed(jobs):
                    try:
                        if job.result():
                            live_ips.add(jobs[job])
                    except Exception:
                        pass

        time.sleep(0.12)
        after = self._windows_neighbors()
        by_ip = {}
        for d in before + after:
            ip = d.get("ip", "")
            if self._in_allowed_networks(ip, networks):
                by_ip[ip] = d
        for ip in live_ips:
            by_ip.setdefault(ip, {
                "type": "LAN", "name": ip, "ip": ip, "mac": "",
                "interface": "", "state": "Online", "source": "Ping discovery"
            })

        hostname = socket.gethostname() or "This PC"
        for row in networks:
            by_ip[row["ip"]] = {
                "type": "This PC", "name": hostname, "ip": row["ip"], "mac": "",
                "interface": row["interface"], "state": "Online", "source": "Local interface"
            }

        devices = sorted(by_ip.values(), key=lambda x: tuple(int(p) for p in x["ip"].split(".")))
        clean_networks = [{k: v for k, v in row.items() if k != "_network"} for row in networks]
        self.last_lan = devices
        if self.security:
            self.security.audit("network.discovery", {"mode": "lan", "active": bool(active), "networks": [n["network"] for n in clean_networks], "devices": len(devices)})
        return ToolResult(True, f"Found {len(devices)} device(s) on the local network.", {"devices": devices, "networks": clean_networks, "active": bool(active)})

    def discover_bluetooth(self):
        if os.name != "nt":
            return ToolResult(False, "Nearby Bluetooth discovery is available on Windows.", {"devices": []})
        ps = (
            "Get-PnpDevice -Class Bluetooth -PresentOnly -ErrorAction SilentlyContinue | "
            "Select-Object FriendlyName,Status,InstanceId | ConvertTo-Json -Compress"
        )
        try:
            p = self._run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps], timeout=12)
            if p.returncode != 0:
                return ToolResult(False, "Windows could not read Bluetooth devices.", {"devices": []})
            raw = p.stdout.strip()
            data = json.loads(raw) if raw else []
            if isinstance(data, dict):
                data = [data]
            devices = []
            seen = set()
            for item in data or []:
                name = str(item.get("FriendlyName") or "Bluetooth device").strip()
                ident = str(item.get("InstanceId") or "")
                key = (name.lower(), ident.lower())
                if key in seen:
                    continue
                seen.add(key)
                devices.append({
                    "type": "Bluetooth",
                    "name": name,
                    "ip": "",
                    "mac": "",
                    "interface": "Bluetooth",
                    "state": str(item.get("Status") or "Present"),
                    "source": "Windows Bluetooth / PnP",
                })
            self.last_bluetooth = devices
            if self.security:
                self.security.audit("network.discovery", {"mode": "bluetooth", "devices": len(devices)})
            return ToolResult(True, f"Found {len(devices)} present/known Bluetooth device(s).", {"devices": devices})
        except Exception as exc:
            return ToolResult(False, "Bluetooth discovery failed: " + str(exc), {"devices": []}, retryable=True)
