# Cloudflare Tunnel Setup Guide

This guide will help you expose your local Document Search API using Cloudflare Tunnel.

## Prerequisites

1. **Cloudflare Account**: Sign up at [cloudflare.com](https://cloudflare.com)
2. **Cloudflare Tunnel**: Install cloudflared CLI tool

## Installation

### Windows (PowerShell)
```powershell
# Download cloudflared
Invoke-WebRequest -Uri "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe" -OutFile "cloudflared.exe"

# Move to a directory in your PATH (optional)
Move-Item cloudflared.exe C:\Windows\System32\
```

### Alternative: Using Chocolatey
```powershell
choco install cloudflared
```

## Setup Steps

### 1. Login to Cloudflare
```bash
cloudflared tunnel login
```
This will open a browser window. Follow the instructions to authenticate.

### 2. Create a Tunnel
```bash
cloudflared tunnel create document-search-api
```

### 3. Configure the Tunnel
Create a config file `tunnel-config.yml`:
```yaml
tunnel: YOUR_TUNNEL_ID
credentials-file: /path/to/your/credentials.json

ingress:
  - hostname: your-subdomain.your-domain.com
    service: http://localhost:8000
  - service: http_status:404
```

### 4. Route Traffic to Your Tunnel
```bash
cloudflared tunnel route dns document-search-api your-subdomain.your-domain.com
```

### 5. Run the Tunnel
```bash
cloudflared tunnel run document-search-api
```

## Quick Start (Temporary Tunnel)

For quick testing, you can create a temporary tunnel:

```bash
cloudflared tunnel --url http://localhost:8000
```

This will give you a temporary URL like: `https://random-string.trycloudflare.com`

## Running Your Application

1. **Start your FastAPI application**:
   ```bash
   python run_local.py
   ```

2. **In another terminal, start the Cloudflare tunnel**:
   ```bash
   cloudflared tunnel --url http://localhost:8000
   ```

3. **Your API will be available at the provided URL**

## Environment Variables

Make sure your `.env` file contains:
```env
GOOGLE_API_KEY=your_google_api_key
DATABASE_URL=sqlite:///./test.db
PORT=8000
```

## Security Considerations

- Your local application runs on `127.0.0.1:8000` (localhost only)
- Cloudflare tunnel provides HTTPS encryption
- Consider adding authentication to your API endpoints
- Monitor your tunnel usage in Cloudflare dashboard

## Troubleshooting

### Common Issues:

1. **Port already in use**: Change the port in your `.env` file
2. **Authentication failed**: Re-run `cloudflared tunnel login`
3. **Tunnel not connecting**: Check if your FastAPI app is running on the correct port

### Useful Commands:
```bash
# List tunnels
cloudflared tunnel list

# Delete a tunnel
cloudflared tunnel delete document-search-api

# Check tunnel status
cloudflared tunnel info document-search-api
```

## Alternative: Using ngrok

If you prefer ngrok:
```bash
# Install ngrok
# Download from https://ngrok.com/download

# Run tunnel
ngrok http 8000
```

## Alternative: Using localtunnel

```bash
# Install localtunnel
npm install -g localtunnel

# Run tunnel
lt --port 8000
``` 