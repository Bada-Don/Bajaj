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

### Main endpoint `/hackrx/run`
The endpoint that actually recieves POST requests
and gives out result:
Input Format:
```json
POST /hackrx/run
Content-Type: application/json
Accept: application/json
Authorization: Bearer 41c2a6a277102861eaaf91a1bd77f852c1c8970e8ec3a5b2d86fdd5960c581e3

{
    "documents": "https://hackrx.blob.core.windows.net/assets/policy.pdf?sv=2023-01-03&st=2025-07-04T09%3A11%3A24Z&se=2027-07-05T09%3A11%3A00Z&sr=b&sp=r&sig=N4a9OU0w0QXO6AOIBiu4bpl7AXvEZogeT%2FjUHNO7HzQ%3D",
    "questions": [
        "What is the grace period for premium payment under the National Parivar Mediclaim Plus Policy?",
        "What is the waiting period for pre-existing diseases (PED) to be covered?",
        "Does this policy cover maternity expenses, and what are the conditions?",
        "What is the waiting period for cataract surgery?",
        "Are the medical expenses for an organ donor covered under this policy?",
        "What is the No Claim Discount (NCD) offered in this policy?",
        "Is there a benefit for preventive health check-ups?",
        "How does the policy define a 'Hospital'?",
        "What is the extent of coverage for AYUSH treatments?",
        "Are there any sub-limits on room rent and ICU charges for Plan A?"
    ]
}
```

Output Format:
```json
{
"answers": [
        "A grace period of thirty days is provided for premium payment after the due date to renew or continue the policy without losing continuity benefits.",
        "There is a waiting period of thirty-six (36) months of continuous coverage from the first policy inception for pre-existing diseases and their direct complications to be covered.",
        "Yes, the policy covers maternity expenses, including childbirth and lawful medical termination of pregnancy. To be eligible, the female insured person must have been continuously covered for at least 24 months. The benefit is limited to two deliveries or terminations during the policy period.",
        "The policy has a specific waiting period of two (2) years for cataract surgery.",
        "Yes, the policy indemnifies the medical expenses for the organ donor's hospitalization for the purpose of harvesting the organ, provided the organ is for an insured person and the donation complies with the Transplantation of Human Organs Act, 1994.",
        "A No Claim Discount of 5% on the base premium is offered on renewal for a one-year policy term if no claims were made in the preceding year. The maximum aggregate NCD is capped at 5% of the total base premium.",
        "Yes, the policy reimburses expenses for health check-ups at the end of every block of two continuous policy years, provided the policy has been renewed without a break. The amount is subject to the limits specified in the Table of Benefits.",
        "A hospital is defined as an institution with at least 10 inpatient beds (in towns with a population below ten lakhs) or 15 beds (in all other places), with qualified nursing staff and medical practitioners available 24/7, a fully equipped operation theatre, and which maintains daily records of patients.",
        "The policy covers medical expenses for inpatient treatment under Ayurveda, Yoga, Naturopathy, Unani, Siddha, and Homeopathy systems up to the Sum Insured limit, provided the treatment is taken in an AYUSH Hospital.",
        "Yes, for Plan A, the daily room rent is capped at 1% of the Sum Insured, and ICU charges are capped at 2% of the Sum Insured. These limits do not apply if the treatment is for a listed procedure in a Preferred Provider Network (PPN)."
    ]
}
```




## How to Run on Google Colab

### 1️⃣ Clone the repository
```bash
!git clone https://github.com/Bada-Don/Bajaj.git
```

### 2️⃣ Install dependencies
```bash
!pip install -r Bajaj/requirements_windows.txt
!pip install python-magic python-dotenv PyPDF2 python-docx faiss-gpu-cu11 rank_bm25
!pip install pyngrok nest_asyncio uvicorn
```

### 3️⃣ Preload documents
```bash
!python Bajaj/preload_doc.py
```

### 4️⃣ Start the API with ngrok tunnel
```python
from pyngrok import ngrok
import nest_asyncio
import subprocess
import time

# ✅ Your ngrok auth token (get it from https://dashboard.ngrok.com/get-started/your-authtoken)
NGROK_AUTH_TOKEN = "ENTER THE ACTUALL NGROK AUTH TOKEN HERE"

# Apply async patch for running in notebooks
nest_asyncio.apply()

# Set auth token
ngrok.set_auth_token(NGROK_AUTH_TOKEN)

# Start your API in the background
process = subprocess.Popen(["python", "Bajaj/run_local.py"])

# Wait for uvicorn to start
time.sleep(20)

# Open the ngrok tunnel
public_url = ngrok.connect(8000)
print("=" * 50)
print("🚀 YOUR PUBLIC API IS LIVE! 🚀")
print(f"Endpoint URL: {public_url}")
print("=" * 50)

# Keep notebook alive until interrupted
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Shutting down...")
    process.terminate()
    ngrok.kill()
```

---

✅ **Note:**  
- Always replace the `NGROK_AUTH_TOKEN` with your own from the [ngrok dashboard](https://dashboard.ngrok.com/get-started/your-authtoken).  
- You must run the API cell **last** so that the notebook stays active while serving your endpoint.


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