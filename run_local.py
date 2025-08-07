#!/usr/bin/env python3
"""
Local development server for the Document Search API
Configured to work with Cloudflare tunnel
"""

import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    # Configuration for local development
    host = "127.0.0.1"  # Localhost only for security
    port = int(os.getenv("PORT", 8000))
    
    print(f"🚀 Starting Document Search API on {host}:{port}")
    print("📝 Make sure to:")
    print("   1. Set up your .env file with required API keys")
    print("   2. Install Cloudflare tunnel: cloudflared tunnel --url http://localhost:8000")
    print("   3. Or use ngrok: ngrok http 8000")
    print("   4. Or use localtunnel: npx localtunnel --port 8000")
    print()
    
    # Run the application
    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        reload=True,  # Enable auto-reload for development
        log_level="info"
    ) 