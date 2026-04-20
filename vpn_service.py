import os
import subprocess
import tempfile
import threading
from typing import Callable, Dict, Optional, Tuple


class VPNService:
    def __init__(self, runner: Callable[..., subprocess.Popen] = subprocess.Popen):
        self._runner = runner
        self._lock = threading.Lock()
        self._process: Optional[subprocess.Popen] = None
        self._auth_file: Optional[str] = None

    def _cleanup_auth_file(self) -> None:
        if self._auth_file and os.path.exists(self._auth_file):
            os.remove(self._auth_file)
        self._auth_file = None

    def status(self) -> Dict[str, Optional[int]]:
        with self._lock:
            connected = bool(self._process and self._process.poll() is None)
            return {
                "connected": connected,
                "pid": self._process.pid if connected else None,
            }

    def connect(
        self,
        config_path: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ) -> Tuple[bool, str]:
        with self._lock:
            if self._process and self._process.poll() is None:
                return False, "VPN is already connected."

            if not config_path:
                return False, "A VPN config path is required."

            absolute_config_path = os.path.abspath(config_path)
            if not os.path.isfile(absolute_config_path):
                return False, f"Config file not found: {absolute_config_path}"

            command = ["openvpn", "--config", absolute_config_path]

            if username or password:
                if not username or not password:
                    return False, "Both username and password are required."
                fd, auth_path = tempfile.mkstemp(prefix="vpn-auth-", text=True)
                os.close(fd)
                with open(auth_path, "w", encoding="utf-8") as auth_file:
                    auth_file.write(f"{username}\n{password}\n")
                os.chmod(auth_path, 0o600)
                self._auth_file = auth_path
                command.extend(["--auth-user-pass", auth_path])

            try:
                self._process = self._runner(
                    command,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return True, "VPN connection started."
            except FileNotFoundError:
                self._cleanup_auth_file()
                self._process = None
                return False, "openvpn binary was not found on the server."
            except Exception as exc:
                self._cleanup_auth_file()
                self._process = None
                return False, f"Failed to start VPN connection: {exc}"

    def disconnect(self) -> Tuple[bool, str]:
        with self._lock:
            if not self._process or self._process.poll() is not None:
                self._process = None
                self._cleanup_auth_file()
                return False, "VPN is not connected."

            process = self._process
            try:
                process.terminate()
                process.wait(timeout=3)
            except Exception:
                process.kill()
                process.wait(timeout=3)

            self._process = None
            self._cleanup_auth_file()
            return True, "VPN disconnected."
