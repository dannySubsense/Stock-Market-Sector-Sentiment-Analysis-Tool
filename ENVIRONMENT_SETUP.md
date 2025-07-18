# 🚀 Environment Setup Guide

## Market Sector Sentiment Analysis Tool - Development Environment

**Target:** Slice 1A Foundation - 8-sector sentiment dashboard  
**Architecture:** FastAPI backend + Next.js frontend + SQLite database  
**Development Mode:** Local development with real API integration

---

## 📋 Prerequisites

### Required Software
- **Python 3.11+** (for FastAPI backend)
- **Node.js 18+** (for Next.js frontend)
- **npm 9+** (package manager)
- **Redis** (for caching - install locally)
- **Git** (version control)

### API Keys Required
- **Polygon.io API key** (Basic/Starter tier)
- **Financial Modeling Prep API key** (Basic tier free)
- **OpenAI API key** (for future AI features)

---

## 🏗️ Directory Structure

```
Stock Market Sector Sentiment Analysis Tool/
├── src/
│   ├── backend/                    # FastAPI backend
│   │   ├── api/routes/            # API endpoints
│   │   ├── core/                  # Configuration & database
│   │   ├── models/                # SQLAlchemy models
│   │   ├── mcp/                   # MCP client integrations
│   │   ├── services/              # Business logic
│   │   └── main.py               # FastAPI app entry point
│   └── frontend/                  # Next.js frontend
│       ├── src/app/              # App Router pages
│       ├── src/components/       # React components
│       └── next.config.js        # Next.js configuration
├── data/                          # SQLite database files
├── tests/                         # Test files
├── credentials.yml                # Your API keys (create from template)
├── credentials.template.yml       # Template for API keys
├── setup.py                      # Automated setup script
├── test_mcp_servers.py           # MCP server test script
└── requirements.txt              # Python dependencies
```

---

## 🔧 Quick Setup

### Option 1: Automated Setup (Recommended)

```bash
# 1. Run the setup script
python setup.py

# 2. Fill in your API keys
cp credentials.template.yml credentials.yml
# Edit credentials.yml with your actual API keys

# 3. Test MCP servers
python test_mcp_servers.py
```

### Option 2: Manual Setup

#### Step 1: Python Backend Setup
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### Step 2: Frontend Setup
```bash
# Install Node.js dependencies
npm install
```

#### Step 3: Database Setup
```bash
# The SQLite database will be created automatically
# Location: ./data/sentiment.db
```

#### Step 4: Redis Setup
```bash
# Install Redis locally
# Windows: Download from https://redis.io/download
# macOS: brew install redis
# Linux: sudo apt-get install redis-server

# Start Redis
redis-server
```

---

## 🔐 Credentials Configuration

### 1. Create credentials.yml
```yaml
# Copy from credentials.template.yml
api_keys:
  polygon:
    key: "your_polygon_api_key_here"
    tier: "basic"
  
  fmp:
    key: "your_fmp_api_key_here"
    tier: "basic"
  
  openai:
    key: "your_openai_api_key_here"
    model: "gpt-4"

database:
  sqlite_path: "./data/sentiment.db"

redis:
  host: "localhost"
  port: 6379
  db: 0

development:
  debug: true
  log_level: "INFO"
```

### 2. API Key Sources
- **Polygon.io:** https://polygon.io/pricing (Basic $29/month or free tier)
- **Financial Modeling Prep:** https://financialmodelingprep.com/developer/docs (Free tier available)
- **OpenAI:** https://platform.openai.com/api-keys (for future AI features)

---

## 🧪 Testing the Setup

### 1. Test MCP Servers
```bash
# This tests both Polygon and FMP API connections
python test_mcp_servers.py
```

Expected output:
```
🔵 Testing Polygon.io MCP Server
✅ Connection successful!
✅ Tickers endpoint working!
✅ Market status endpoint working!

🟡 Testing FMP MCP Server  
✅ Connection successful!
✅ Stock list endpoint working!
✅ Company profile working!

🚀 Testing Small-Cap Workflow
✅ Small-cap workflow test completed!

🎉 All tests passed! MCP servers are working correctly.
```

### 2. Test Backend
```bash
# Start the backend
cd src/backend
python main.py

# Test health endpoint
curl http://localhost:8000/health
```

### 3. Test Frontend
```bash
# Start the frontend
npm run dev

# Visit http://localhost:3000
```

---

## 🚦 Running the Application

### Development Mode

#### Terminal 1: Backend
```bash
# Activate virtual environment
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Start FastAPI backend
cd src/backend
python main.py

# Backend will run on http://localhost:8000
```

#### Terminal 2: Frontend
```bash
# Start Next.js frontend
npm run dev

# Frontend will run on http://localhost:3000
```

#### Terminal 3: Redis
```bash
# Start Redis server
redis-server

# Redis will run on localhost:6379
```

---

## 📊 API Endpoints

### Health Check
- `GET /health` - Overall system health
- `GET /health/database` - Database status  
- `GET /health/redis` - Redis status
- `GET /health/apis` - External API status

### Sectors
- `GET /api/sectors` - Get all sector sentiment
- `GET /api/sectors/{sector_name}` - Get specific sector details
- `POST /api/sectors/refresh` - Trigger on-demand analysis

### Stocks
- `GET /api/stocks` - Get stocks with filtering
- `GET /api/stocks/{symbol}` - Get specific stock details
- `GET /api/stocks/universe/stats` - Get universe statistics

---

## 🔍 Troubleshooting

### Common Issues

#### 1. "No credentials configured"
**Solution:** Create `credentials.yml` from `credentials.template.yml` and add your API keys

#### 2. "Connection failed" in MCP tests
**Solution:** Verify your API keys are correct and have sufficient quota

#### 3. "Redis connection failed"
**Solution:** Start Redis server with `redis-server`

#### 4. "Module not found" errors
**Solution:** Activate virtual environment and reinstall dependencies

#### 5. Frontend TypeScript errors
**Solution:** Run `npm run type-check` to verify TypeScript setup

### Debug Mode
Enable debug mode in `credentials.yml`:
```yaml
development:
  debug: true
  log_level: "DEBUG"
```

---

## 🎯 Next Steps for Slice 1A Development

### 1. Core Features to Implement
- [ ] Stock universe filtering (1,500 small caps)
- [ ] Sector sentiment calculation engine
- [ ] Multi-timeframe analysis (30min, 1D, 3D, 1W)
- [ ] Top 3 bullish/bearish stock ranking
- [ ] Real-time WebSocket updates

### 2. Background Analysis Scheduler
- [ ] 8PM comprehensive analysis
- [ ] 4AM pre-market updates
- [ ] 8AM economic data integration
- [ ] On-demand refresh system

### 3. Frontend Development
- [ ] Sector grid component
- [ ] Real-time data integration
- [ ] Color-coded sentiment display
- [ ] Stock detail modals

---

## 📈 Performance Targets

### Slice 1A Goals
- **Sector Grid Loading:** <1 second
- **On-Demand Analysis:** 3-5 minutes
- **Database Queries:** <500ms
- **Universe Coverage:** 1,500+ stocks
- **Directional Accuracy:** 75%+

---

## 📞 Support

If you encounter issues:
1. Check this setup guide
2. Run `python test_mcp_servers.py` to verify API connections
3. Check logs in the backend console
4. Verify all dependencies are installed correctly

**Environment setup complete!** You're ready to begin Slice 1A development. 