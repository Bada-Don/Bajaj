# Document Search API - Local Development Setup

This guide will help you run the Document Search API locally on your PC and expose it using Cloudflare tunnel.

## 🚀 Quick Start

### 1. Install Dependencies

**For Windows:**
```bash
pip install -r requirements_windows.txt
```

**For Linux/Mac:**
```bash
pip install -r requirements.txt
```

### 2. Set Up Environment Variables
Copy `env_example.txt` to `.env` and fill in your API keys:
```bash
cp env_example.txt .env
```

Edit `.env` and add your Google API key:
```env
GOOGLE_API_KEY=your_actual_google_api_key
```

### 3. Start the Application

**Option A: Using the batch file (Windows)**
```bash
start_local.bat
```

**Option B: Using PowerShell script (Windows)**
```powershell
.\start_local.ps1
```

**Option C: Using Python directly**
```bash
python run_local.py
```

### 4. Expose with Cloudflare Tunnel
In a new terminal:
```bash
cloudflared tunnel --url http://localhost:8000
```

## 📋 Prerequisites

- Python 3.8+
- Google API Key for Gemini
- Cloudflare account (for tunnel)

## 🔧 Installation Steps

### 1. Python Setup
Make sure Python is installed and in your PATH.

### 2. Install Cloudflare Tunnel
**Windows (PowerShell):**
```powershell
Invoke-WebRequest -Uri "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe" -OutFile "cloudflared.exe"
```

**Alternative (Chocolatey):**
```powershell
choco install cloudflared
```

### 3. Get Google API Key
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Add it to your `.env` file

## 🏃‍♂️ Running the Application

### Method 1: Simple Start
```bash
python run_local.py
```

### Method 2: Windows Batch File
```bash
start_local.bat
```

### Method 3: Direct Uvicorn
```bash
uvicorn app:app --host 127.0.0.1 --port 8000 --reload
```

## 🌐 Exposing Your Local Server

### Option 1: Cloudflare Tunnel (Recommended)
```bash
# Quick temporary tunnel
cloudflared tunnel --url http://localhost:8000

# Or create a permanent tunnel
cloudflared tunnel create my-api
cloudflared tunnel route dns my-api your-subdomain.yourdomain.com
cloudflared tunnel run my-api
```

### Option 2: ngrok
```bash
ngrok http 8000
```

### Option 3: localtunnel
```bash
npx localtunnel --port 8000
```

## 📡 API Endpoints

Once running, your API will be available at:
- **Local**: http://localhost:8000
- **Public**: https://your-tunnel-url.com

### Available Endpoints:
- `GET /health` - Health check
- `POST /upload-url` - Upload document from URL
- `POST /upload-file` - Upload document file
- `POST /search` - Search documents
- `POST /hackrx/run` - Process multiple questions

### API Documentation:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔒 Security Considerations

1. **Local Access Only**: The app runs on `127.0.0.1` (localhost only)
2. **HTTPS via Tunnel**: Cloudflare provides SSL encryption
3. **API Key Protection**: Keep your `.env` file secure
4. **Firewall**: Consider firewall rules for additional security

## 🛠️ Configuration

### Environment Variables
Key variables in `.env`:
- `GOOGLE_API_KEY`: Your Google Gemini API key
- `DATABASE_URL`: Database connection string
- `PORT`: Server port (default: 8000)

### Database Options
- **SQLite** (default): `sqlite:///./test.db`
- **PostgreSQL**: `postgresql://user:pass@localhost:5432/dbname`

## 🐛 Troubleshooting

### Common Issues:

1. **Port Already in Use**
   ```bash
   # Change port in .env
   PORT=8001
   ```

2. **Missing Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **API Key Issues**
   - Verify your Google API key is correct
   - Check if you have sufficient quota

4. **Tunnel Connection Issues**
   - Ensure your app is running on the correct port
   - Check Cloudflare tunnel status

### Logs
The application logs to console. Check for:
- Service initialization messages
- Error messages
- API request logs

## 📊 Monitoring

### Health Check
```bash
curl http://localhost:8000/health
```

### Service Status
The `/health` endpoint returns:
```json
{
  "status": "healthy",
  "models_loaded": true
}
```

## 🔄 Development Workflow

1. **Start Development Server**:
   ```bash
   python run_local.py
   ```

2. **Start Tunnel** (in another terminal):
   ```bash
   cloudflared tunnel --url http://localhost:8000
   ```

3. **Test Your API**:
   - Use the provided URL from Cloudflare
   - Test endpoints via Swagger UI
   - Monitor logs in both terminals

4. **Stop Services**:
   - Press `Ctrl+C` in both terminals

## 📝 Notes

- The application uses SQLite by default for simplicity
- All models are loaded on startup
- File uploads are limited to 10MB
- The app supports auto-reload during development

## 🆘 Support

If you encounter issues:
1. Check the logs for error messages
2. Verify all environment variables are set
3. Ensure all dependencies are installed
4. Check if the port is available

For more detailed setup instructions, see `cloudflare_tunnel.md`. 