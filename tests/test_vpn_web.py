from app import create_app
from vpn_service import VPNService


class FakeProcess:
    def __init__(self):
        self.pid = 12345
        self._return_code = None

    def poll(self):
        return self._return_code

    def terminate(self):
        self._return_code = 0

    def kill(self):
        self._return_code = 137

    def wait(self, timeout=None):
        return self._return_code


def test_vpn_service_connect_and_disconnect(tmp_path):
    calls = []
    config = tmp_path / "client.ovpn"
    config.write_text("client\n", encoding="utf-8")

    def runner(command, **kwargs):
        calls.append(command)
        return FakeProcess()

    service = VPNService(runner=runner)
    ok, msg = service.connect(str(config))
    assert ok is True
    assert msg == "VPN connection started."
    assert calls[0][:3] == ["openvpn", "--config", str(config)]
    assert service.status()["connected"] is True

    ok, msg = service.disconnect()
    assert ok is True
    assert msg == "VPN disconnected."
    assert service.status()["connected"] is False


def test_vpn_service_requires_existing_config(tmp_path):
    service = VPNService(runner=lambda *args, **kwargs: FakeProcess())
    ok, msg = service.connect(str(tmp_path / "missing.ovpn"))
    assert ok is False
    assert "Config file not found" in msg


class StubWebService:
    def __init__(self):
        self.connected = False

    def status(self):
        return {"connected": self.connected, "pid": 999 if self.connected else None}

    def connect(self, config_path, username=None, password=None):
        self.connected = True
        return True, f"VPN connected using {config_path}"

    def disconnect(self):
        self.connected = False
        return True, "VPN disconnected."


def test_web_routes_connect_disconnect_and_status():
    app = create_app(vpn_service=StubWebService())
    app.config["TESTING"] = True
    client = app.test_client()

    res = client.get("/api/status")
    assert res.status_code == 200
    assert res.get_json()["connected"] is False

    res = client.post(
        "/connect",
        data={"config_path": "/etc/openvpn/client.ovpn", "username": "", "password": ""},
        follow_redirects=True,
    )
    assert res.status_code == 200
    assert b"VPN connected using /etc/openvpn/client.ovpn" in res.data

    res = client.get("/api/status")
    assert res.get_json()["connected"] is True

    res = client.post("/disconnect", follow_redirects=True)
    assert res.status_code == 200
    assert b"VPN disconnected." in res.data
