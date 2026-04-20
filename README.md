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

4. Open `http://<server-ip>:8000` and use the form to connect.

## Notes

- Enter the full path to your `.ovpn` file on the server.
- If your config needs credentials, provide username/password in the form.
- API status endpoint: `GET /api/status`
