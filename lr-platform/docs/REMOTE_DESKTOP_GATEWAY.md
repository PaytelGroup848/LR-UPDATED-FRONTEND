# Remote Desktop Gateway

LR Remote uses Apache Guacamole as the HTML5 remote desktop gateway. The user
portal can show assigned applications without Guacamole, but browser streaming
requires these backend environment variables:

```env
GUACAMOLE_URL=http://127.0.0.1:8080/guacamole
GUACAMOLE_PUBLIC_URL=http://127.0.0.1:8080/guacamole
GUACAMOLE_USER=guacadmin
GUACAMOLE_PASSWORD=change-this-password
GUACAMOLE_DATA_SOURCE=default
FRONTEND_URL=http://127.0.0.1:3000
```

After changing `.env`, restart the backend.

If Guacamole logs an error like `Invalid character found in method name
[0x16...]`, the browser/proxy is sending HTTPS traffic to Guacamole's plain HTTP
Tomcat port. With the Docker Compose service in this repo, port `8080` is HTTP:

```env
GUACAMOLE_URL=http://host.docker.internal:8080/guacamole
GUACAMOLE_PUBLIC_URL=http://YOUR_SERVER_IP:8080/guacamole
```

Open `http://YOUR_SERVER_IP:8080/guacamole`, not
`https://YOUR_SERVER_IP:8080/guacamole`. Use an `https://` public URL only when
you have put Guacamole behind a TLS reverse proxy that forwards to the
container's HTTP port.

When these values are blank, launch requests still create a pending session and
the portal downloads an `.rdp` fallback file. That fallback opens with the local
Windows Remote Desktop client. For TSplus-style HTML5 browser streaming,
Guacamole must be running and reachable from the backend.

The Windows server must also allow RDP connections and the server record in the
Admin Panel must have the correct host, port, username, and password.
