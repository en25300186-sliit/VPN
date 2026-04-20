# VPN Web Service (Python)

This repository now contains a minimal Python VPN control service with a web UI.

## What it does

- Hosts a website using Flask
- Lets you connect/disconnect an OpenVPN tunnel from the website
- Shows VPN connection status in the UI and through a JSON endpoint

## Run on a server

1. Install OpenVPN on the server (`openvpn` must be in `PATH`).
2. Install Python dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Start the service:

   ```bash
   python app.py
   ```

4. Optional security settings:

   ```bash
   export FLASK_SECRET_KEY="replace-with-strong-random-secret"
   export VPN_WEB_TOKEN="replace-with-control-panel-token"
   export VPN_CONFIG_DIR="/etc/openvpn"
   export VPN_LOG_PATH="/var/log/vpn-service.log"
   ```

5. Open `http://127.0.0.1:8000` on the server (or set `HOST=0.0.0.0` if you explicitly want remote access).

## Notes

- Enter the full path to your `.ovpn` file on the server.
- For safety, set `VPN_CONFIG_DIR` so config paths are restricted to that directory.
- OpenVPN usually requires elevated privileges to create the tunnel interface.
- Use an `.ovpn` file that already contains the required auth settings.
- If `VPN_LOG_PATH` is set, OpenVPN output is appended to that file.
- If `FLASK_SECRET_KEY` is not set, the service uses an ephemeral key and existing sessions are invalidated on restart.
- API status endpoint: `GET /api/status`
