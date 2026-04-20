import os
import subprocess
import threading
from pathlib import Path
from typing import Callable, Dict, Optional, TextIO, Tuple


class VPNService:
    TERMINATE_TIMEOUT_SECONDS = 3

    def __init__(
        self,
        runner: Callable[..., subprocess.Popen] = subprocess.Popen,
        allowed_config_dir: Optional[str] = None,
        log_path: Optional[str] = None,
    ):
        self._runner = runner
        self._lock = threading.Lock()
        self._process: Optional[subprocess.Popen] = None
        self._allowed_config_dir = (
            Path(allowed_config_dir).resolve() if allowed_config_dir else None
        )
        self._log_path = str(Path(log_path).resolve()) if log_path else None
        self._log_file: Optional[TextIO] = None

    def _close_log_file(self) -> None:
        if self._log_file:
            self._log_file.close()
            self._log_file = None

    def status(self) -> Dict[str, object]:
        with self._lock:
            connected = bool(self._process and self._process.poll() is None)
            if not connected:
                self._close_log_file()
            return {
                "connected": connected,
                "pid": self._process.pid if connected else None,
            }

    def connect(
        self,
        config_path: str,
    ) -> Tuple[bool, str]:
        with self._lock:
            if self._process and self._process.poll() is None:
                return False, "VPN is already connected."

            if not config_path:
                return False, "A VPN config path is required."

            absolute_config_path = Path(config_path).resolve()
            if not absolute_config_path.is_file():
                return False, f"Config file not found: {absolute_config_path}"
            if self._allowed_config_dir:
                try:
                    absolute_config_path.relative_to(self._allowed_config_dir)
                except ValueError:
                    return (
                        False,
                        f"Config path must be inside: {self._allowed_config_dir}",
                    )

            command = ["openvpn", "--config", str(absolute_config_path)]

            try:
                output_stream = subprocess.DEVNULL
                if self._log_path:
                    try:
                        self._log_file = open(self._log_path, "ab")
                        os.chmod(self._log_path, 0o600)
                    except OSError as exc:
                        return False, f"Failed to open VPN log file: {exc}"
                    output_stream = self._log_file
                self._process = self._runner(
                    command,
                    stdout=output_stream,
                    stderr=output_stream,
                )
                return True, "VPN connection started."
            except FileNotFoundError:
                self._close_log_file()
                self._process = None
                return False, "openvpn binary was not found on the server."
            except Exception as exc:
                self._close_log_file()
                self._process = None
                return False, f"Failed to start VPN connection: {exc}"

    def disconnect(self) -> Tuple[bool, str]:
        with self._lock:
            if not self._process or self._process.poll() is not None:
                self._process = None
                return False, "VPN is not connected."

            process = self._process
            try:
                process.terminate()
                process.wait(timeout=self.TERMINATE_TIMEOUT_SECONDS)
            except subprocess.TimeoutExpired:
                process.kill()
                try:
                    process.wait(timeout=self.TERMINATE_TIMEOUT_SECONDS)
                except subprocess.TimeoutExpired:
                    return False, "Failed to stop VPN process cleanly."

            self._process = None
            self._close_log_file()
            return True, "VPN disconnected."
