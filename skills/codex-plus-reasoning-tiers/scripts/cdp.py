"""Minimal Chrome DevTools Protocol client using only the standard library.

Codex++ injects a renderer script that exposes
``window.__codexSessionDeleteBridge(route, payload)``. That bridge is the only
safe way to mutate Codex++ settings while the app is running, because the app
holds settings in memory and rewrites settings.json from that copy.
"""

from __future__ import annotations

import base64
import json
import os
import socket
import struct
import subprocess
import sys
import urllib.error
import urllib.request

DEFAULT_PORTS = tuple(range(9222, 9236))


class CdpError(RuntimeError):
    pass


def _http_json(url: str, timeout: float = 3.0):
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def candidate_ports() -> list[int]:
    """Ports worth probing, derived from the running Codex++ command line."""
    ports: list[int] = []
    if os.name == "nt":
        cmd = (
            "Get-CimInstance Win32_Process -Filter \"Name='codex-plus-plus.exe'\" "
            "| Select-Object -ExpandProperty CommandLine"
        )
        try:
            out = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", cmd],
                capture_output=True,
                text=True,
                timeout=20,
            ).stdout
        except (OSError, subprocess.SubprocessError):
            out = ""
        for token in out.split():
            if token.startswith("--debug-port"):
                value = token.split("=", 1)[1] if "=" in token else ""
                if value.isdigit():
                    ports.append(int(value))
        # "--debug-port 9229" style
        parts = out.split()
        for index, part in enumerate(parts[:-1]):
            if part == "--debug-port" and parts[index + 1].isdigit():
                ports.append(int(parts[index + 1]))
    for port in DEFAULT_PORTS:
        if port not in ports:
            ports.append(port)
    return ports


def find_page_target() -> tuple[int, str]:
    """Return (port, websocket_url) for the Codex app page target."""
    for port in candidate_ports():
        try:
            targets = _http_json(f"http://127.0.0.1:{port}/json/list")
        except (urllib.error.URLError, OSError, ValueError):
            continue
        for target in targets:
            if target.get("type") != "page":
                continue
            url = str(target.get("url", ""))
            ws = target.get("webSocketDebuggerUrl")
            if ws and url.startswith("app://"):
                return port, ws
    raise CdpError(
        "未找到 Codex 调试页面。请确认 Codex++ 正在运行，且启动参数包含 --debug-port。"
    )


class WebSocket:
    def __init__(self, url: str, timeout: float = 30.0):
        if not url.startswith("ws://"):
            raise CdpError(f"仅支持 ws:// 调试地址，收到 {url}")
        rest = url[len("ws://"):]
        host_port, _, path = rest.partition("/")
        host, _, port = host_port.partition(":")
        self.sock = socket.create_connection((host, int(port or 80)), timeout=timeout)
        self.sock.settimeout(timeout)
        key = base64.b64encode(os.urandom(16)).decode()
        handshake = (
            f"GET /{path} HTTP/1.1\r\n"
            f"Host: {host_port}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            "Sec-WebSocket-Version: 13\r\n\r\n"
        )
        self.sock.sendall(handshake.encode())
        self._buffer = b""
        response = self._read_until(b"\r\n\r\n")
        if b"101" not in response.split(b"\r\n", 1)[0]:
            raise CdpError(f"WebSocket 握手失败：{response[:120]!r}")

    def _read_until(self, marker: bytes) -> bytes:
        while marker not in self._buffer:
            chunk = self.sock.recv(65536)
            if not chunk:
                raise CdpError("调试连接已断开")
            self._buffer += chunk
        head, _, self._buffer = self._buffer.partition(marker)
        return head + marker

    def _recv_exact(self, count: int) -> bytes:
        while len(self._buffer) < count:
            chunk = self.sock.recv(65536)
            if not chunk:
                raise CdpError("调试连接已断开")
            self._buffer += chunk
        data, self._buffer = self._buffer[:count], self._buffer[count:]
        return data

    def send(self, text: str) -> None:
        payload = text.encode("utf-8")
        header = bytearray([0x81])
        length = len(payload)
        if length < 126:
            header.append(0x80 | length)
        elif length < 65536:
            header.append(0x80 | 126)
            header += struct.pack("!H", length)
        else:
            header.append(0x80 | 127)
            header += struct.pack("!Q", length)
        mask = os.urandom(4)
        header += mask
        masked = bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload))
        self.sock.sendall(bytes(header) + masked)

    def recv(self) -> str:
        while True:
            first, second = self._recv_exact(2)
            opcode = first & 0x0F
            length = second & 0x7F
            if length == 126:
                length = struct.unpack("!H", self._recv_exact(2))[0]
            elif length == 127:
                length = struct.unpack("!Q", self._recv_exact(8))[0]
            data = self._recv_exact(length) if length else b""
            if opcode == 0x8:
                raise CdpError("调试连接被对端关闭")
            if opcode == 0x9:  # ping
                continue
            if opcode in (0x1, 0x2):
                return data.decode("utf-8", "replace")

    def close(self) -> None:
        try:
            self.sock.close()
        except OSError:
            pass


class CdpSession:
    def __init__(self) -> None:
        self.port, ws_url = find_page_target()
        self.ws = WebSocket(ws_url)
        self._id = 0

    def evaluate(self, expression: str, await_promise: bool = True):
        self._id += 1
        message = {
            "id": self._id,
            "method": "Runtime.evaluate",
            "params": {
                "expression": expression,
                "returnByValue": True,
                "awaitPromise": await_promise,
            },
        }
        self.ws.send(json.dumps(message))
        while True:
            payload = json.loads(self.ws.recv())
            if payload.get("id") != self._id:
                continue
            if "error" in payload:
                raise CdpError(f"CDP 调用失败：{payload['error']}")
            result = payload.get("result", {})
            if result.get("exceptionDetails"):
                raise CdpError(f"页面脚本异常：{result['exceptionDetails']}")
            return result.get("result", {}).get("value")

    def bridge(self, route: str, payload: dict | None = None):
        """Call window.__codexSessionDeleteBridge(route, payload)."""
        expression = (
            "(async()=>{try{"
            f"const r=await window.__codexSessionDeleteBridge({json.dumps(route)},"
            f"{json.dumps(payload or {})});"
            "return JSON.stringify({ok:true,value:r});"
            "}catch(e){return JSON.stringify({ok:false,error:String(e&&e.message||e)});}})()"
        )
        raw = self.evaluate(expression)
        parsed = json.loads(raw) if raw else {"ok": False, "error": "空响应"}
        if not parsed.get("ok"):
            raise CdpError(parsed.get("error", "桥接调用失败"))
        return parsed.get("value")

    def close(self) -> None:
        self.ws.close()


def probe() -> dict:
    """Report whether the live bridge is reachable."""
    try:
        session = CdpSession()
    except CdpError as error:
        return {"available": False, "reason": str(error)}
    try:
        settings = session.bridge("/settings/get")
        return {
            "available": True,
            "port": session.port,
            "active_relay_id": settings.get("activeRelayId", ""),
        }
    finally:
        session.close()


if __name__ == "__main__":
    print(json.dumps(probe(), ensure_ascii=False, indent=2))
    sys.exit(0)
