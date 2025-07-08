# 📊 Stock Market Sector Sentiment Analysis Agent

> AI-powered sector-first sentiment analysis platform for small-cap traders with multi-agent orchestration

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Next.js](https://img.shields.io/badge/Next.js-14-black.svg)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)](https://fastapi.tiangolo.com/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-blue.svg)](https://www.typescriptlang.org/)

## 🎯 Project Overview

**"From Sector Sentiment to Trade Decision in Under 10 Seconds"**

This platform transforms how traders identify small-cap opportunities through AI-powered agent orchestration and real-time market intelligence. Built with a sector-first approach, it provides color-coded sentiment analysis, 10-point shortability scoring, and gap opportunity detection.

### ⚡ Key Features

- 🎛️ **Sector Sentiment Dashboard** - Real-time color-coded grid (🔴/🟡/🔵/🟢)
- 🤖 **AI Agent Orchestration** - 6 parallel agents for comprehensive analysis
- 🎯 **10-Point Shortability Dial** - Visual risk assessment with historical tracking
- 📈 **Gap Analysis Tool** - Automated detection of 15%+ price movements
- 🔍 **Background Scanner** - 15-minute automated opportunity identification
- 📋 **SEC Filing Monitor** - Real-time regulatory event alerts

### 🏗️ Architecture

```
User Interface (Next.js + DaisyUI)
    ↓
Agent Orchestrator (FastAPI)
    ↓
[6 Parallel AI Agents]
    ↓
MCP Server Layer (Polygon.io, News, Economic Data)
    ↓
Data Layer (PostgreSQL + TimescaleDB + Redis)
```

## 🚀 Getting Started

### Prerequisites

- Node.js 18+ and npm
- Python 3.11+
- PostgreSQL 15+
- Redis 7+

### 📋 Development Setup

```bash
# Clone the repository (update YOUR_USERNAME with your actual GitHub username)
git clone https://github.com/YOUR_USERNAME/stock-market-sentiment-agent.git
cd stock-market-sentiment-agent

# Install frontend dependencies
cd src/frontend
npm install

# Install backend dependencies
cd ../backend
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys
```

### 🔧 Environment Variables

```env
# API Keys
POLYGON_API_KEY=your_polygon_api_key
OPENAI_API_KEY=your_openai_api_key

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/sentiment_db
REDIS_URL=redis://localhost:6379

# Development
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 🎯 Target Users

### 📈 Primary: Active Intraday Traders
- Experienced traders, $25K+ trading capital
- Focus on small-cap momentum
- Need systematic sector sentiment analysis

### 📊 Secondary: Part-time Swing Traders
- Supplemental income focus
- Risk-conscious approach
- Require quick decision frameworks

## 📈 Performance Targets

| Metric | Target |
|--------|--------|
| Analysis Speed | <5 seconds complete stock analysis |
| User Engagement | 90%+ engage with sector grid in 30s |
| System Uptime | 99.5% during market hours |
| User Satisfaction | 80%+ with AI-generated thesis |

## 🗺️ Development Roadmap

### Phase 1: MVP Foundation (Weeks 1-4)
- [x] Project setup and architecture
- [ ] Sector sentiment dashboard
- [ ] Basic AI agent orchestration
- [ ] Polygon.io integration

### Phase 2: AI Agent Integration (Weeks 5-8)
- [ ] Multi-agent orchestration system
- [ ] 10-point shortability dial
- [ ] Investment thesis generation
- [ ] WebSocket real-time updates

### Phase 3: Advanced Analytics (Weeks 9-12)
- [ ] Gap analysis tool
- [ ] Background watchlist scanner
- [ ] SEC filing monitor
- [ ] Performance optimization

### Phase 4: Production Polish (Weeks 13-16)
- [ ] User authentication
- [ ] Mobile optimization
- [ ] Comprehensive testing
- [ ] Production deployment

## 🔧 Tech Stack

### Frontend
- **Next.js 14** with App Router and SSR
- **TypeScript** for type safety
- **Tailwind CSS + DaisyUI** for styling
- **WebSocket** for real-time updates

### Backend
- **FastAPI** for high-performance API
- **PostgreSQL + TimescaleDB** for time-series data
- **Redis** for caching and real-time features
- **MCP Protocol** for agent orchestration

### AI & Data
- **OpenAI GPT-4** for investment thesis generation
- **FinBERT** for financial sentiment analysis
- **Polygon.io** for real-time market data
- **SEC EDGAR** for regulatory filings

## 📚 Documentation

- [📋 Product Requirements Document](./PRODUCT-REQUIREMENTS.md)
- [🏗️ Technical Architecture](./ARCHITECTURE.md)
- [🔌 API Documentation](./API_DOCUMENTATION.md)
- [🧪 Testing Guide](./TESTING.md)

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🚨 Disclaimer

This software is for educational and research purposes only. It is not intended as financial advice. Always conduct your own research and consult with qualified financial professionals before making investment decisions.

## 🔗 Links

- [Live Demo](https://stock-market-sentiment-agent.vercel.app) (Coming Soon)
- [Documentation](./docs/)
- [Issue Tracker](https://github.com/YOUR_USERNAME/stock-market-sentiment-agent/issues)

---

**Built with ❤️ for the trading community** 