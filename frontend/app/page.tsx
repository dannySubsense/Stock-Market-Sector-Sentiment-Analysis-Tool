import SectorGrid from '../components/SectorGrid';

export default function Home() {
  return (
    <div className="space-y-8">
      <header className="text-center">
        <h1 className="text-4xl font-bold text-text-primary mb-2">
          Market Sector Sentiment Analysis Tool
        </h1>
        <p className="text-text-secondary text-lg">
          AI-powered sector-first sentiment analysis platform for small-cap traders
        </p>
      </header>

      <SectorGrid />

      <div className="text-center text-text-secondary">
        <p className="text-sm">
          Environment setup complete! Connect to backend APIs to see real data.
        </p>
        <p className="text-sm">
          Backend: <a href="http://localhost:8000" target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:underline">http://localhost:8000</a>
        </p>
      </div>
    </div>
  );
} 