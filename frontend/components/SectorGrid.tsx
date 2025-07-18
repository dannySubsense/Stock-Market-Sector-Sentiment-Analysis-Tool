/**
 * Sector Grid Component - Slice 1A Implementation
 * Color-coded 8-sector dashboard grid with multi-timeframe analysis
 * Displays sentiment, top stocks, and trading signals
 */
'use client';

import React, { useState, useEffect } from 'react';
import { ChevronRightIcon, TrendingUpIcon, TrendingDownIcon, RefreshCwIcon } from 'lucide-react';

// Types for sector data
interface TimeframeScores {
  '30min': number;
  '1day': number;
  '3day': number;
  '1week': number;
}

interface TopStock {
  symbol: string;
  change_percent: number;
  volume_ratio: number;
}

interface SectorData {
  sector: string;
  sentiment_score: number;
  color_classification: 'dark_red' | 'light_red' | 'blue_neutral' | 'light_green' | 'dark_green';
  trading_signal: string;
  confidence_level: number;
  timeframe_scores: TimeframeScores;
  russell_comparison?: TimeframeScores; // Optional since backend doesn't return it yet
  stock_count: number;
  last_updated: string;
  top_bullish?: TopStock[];
  top_bearish?: TopStock[];
}

interface SectorGridProps {
  sectors?: SectorData[];
  onSectorClick?: (sector: string) => void;
  onRefresh?: () => void;
  isLoading?: boolean;
  lastUpdated?: string;
}

// Color mappings for sectors
const sectorColorClasses = {
  'dark_red': 'bg-gradient-to-br from-red-600 to-red-700 border-red-500 text-white',
  'light_red': 'bg-gradient-to-br from-red-400 to-red-500 border-red-400 text-white',
  'blue_neutral': 'bg-gradient-to-br from-blue-500 to-blue-600 border-blue-400 text-white',
  'light_green': 'bg-gradient-to-br from-green-400 to-green-500 border-green-400 text-white',
  'dark_green': 'bg-gradient-to-br from-green-600 to-green-700 border-green-500 text-white'
};

// Trading signal display
const tradingSignalDisplay = {
  'PRIME_SHORTING_ENVIRONMENT': { text: 'PRIME SHORT', icon: '🔴', color: 'text-red-200' },
  'GOOD_SHORTING_ENVIRONMENT': { text: 'GOOD SHORT', icon: '🟠', color: 'text-orange-200' },
  'NEUTRAL_CAUTIOUS': { text: 'NEUTRAL', icon: '🔵', color: 'text-blue-200' },
  'AVOID_SHORTS': { text: 'AVOID SHORTS', icon: '🟡', color: 'text-yellow-200' },
  'DO_NOT_SHORT': { text: 'DO NOT SHORT', icon: '🟢', color: 'text-green-200' }
};

// Sector display names
const sectorDisplayNames = {
  'technology': 'Technology',
  'healthcare': 'Healthcare',
  'energy': 'Energy',
  'financial': 'Financial',
  'consumer_discretionary': 'Consumer',
  'industrials': 'Industrials',
  'materials': 'Materials',
  'utilities': 'Utilities'
};

// Default sectors for loading state
const defaultSectors: SectorData[] = [
  {
    sector: 'technology',
    sentiment_score: 0.0,
    color_classification: 'blue_neutral',
    confidence_level: 0.0,
    stock_count: 0,
    trading_signal: 'NEUTRAL_CAUTIOUS',
    timeframe_scores: { '30min': 0, '1day': 0, '3day': 0, '1week': 0 },
    last_updated: new Date().toISOString(),
    top_bullish: [],
    top_bearish: []
  },
  {
    sector: 'healthcare',
    sentiment_score: 0.0,
    color_classification: 'blue_neutral',
    confidence_level: 0.0,
    stock_count: 0,
    trading_signal: 'NEUTRAL_CAUTIOUS',
    timeframe_scores: { '30min': 0, '1day': 0, '3day': 0, '1week': 0 },
    last_updated: new Date().toISOString(),
    top_bullish: [],
    top_bearish: []
  },
  {
    sector: 'energy',
    sentiment_score: 0.0,
    color_classification: 'blue_neutral',
    confidence_level: 0.0,
    stock_count: 0,
    trading_signal: 'NEUTRAL_CAUTIOUS',
    timeframe_scores: { '30min': 0, '1day': 0, '3day': 0, '1week': 0 },
    last_updated: new Date().toISOString(),
    top_bullish: [],
    top_bearish: []
  },
  {
    sector: 'financial',
    sentiment_score: 0.0,
    color_classification: 'blue_neutral',
    confidence_level: 0.0,
    stock_count: 0,
    trading_signal: 'NEUTRAL_CAUTIOUS',
    timeframe_scores: { '30min': 0, '1day': 0, '3day': 0, '1week': 0 },
    last_updated: new Date().toISOString(),
    top_bullish: [],
    top_bearish: []
  },
  {
    sector: 'consumer_discretionary',
    sentiment_score: 0.0,
    color_classification: 'blue_neutral',
    confidence_level: 0.0,
    stock_count: 0,
    trading_signal: 'NEUTRAL_CAUTIOUS',
    timeframe_scores: { '30min': 0, '1day': 0, '3day': 0, '1week': 0 },
    last_updated: new Date().toISOString(),
    top_bullish: [],
    top_bearish: []
  },
  {
    sector: 'industrials',
    sentiment_score: 0.0,
    color_classification: 'blue_neutral',
    confidence_level: 0.0,
    stock_count: 0,
    trading_signal: 'NEUTRAL_CAUTIOUS',
    timeframe_scores: { '30min': 0, '1day': 0, '3day': 0, '1week': 0 },
    last_updated: new Date().toISOString(),
    top_bullish: [],
    top_bearish: []
  },
  {
    sector: 'materials',
    sentiment_score: 0.0,
    color_classification: 'blue_neutral',
    confidence_level: 0.0,
    stock_count: 0,
    trading_signal: 'NEUTRAL_CAUTIOUS',
    timeframe_scores: { '30min': 0, '1day': 0, '3day': 0, '1week': 0 },
    last_updated: new Date().toISOString(),
    top_bullish: [],
    top_bearish: []
  },
  {
    sector: 'utilities',
    sentiment_score: 0.0,
    color_classification: 'blue_neutral',
    confidence_level: 0.0,
    stock_count: 0,
    trading_signal: 'NEUTRAL_CAUTIOUS',
    timeframe_scores: { '30min': 0, '1day': 0, '3day': 0, '1week': 0 },
    last_updated: new Date().toISOString(),
    top_bullish: [],
    top_bearish: []
  }
];

const SectorCard: React.FC<{
  sector: SectorData;
  onClick: (sector: string) => void;
  isLoading: boolean;
}> = ({ sector, onClick, isLoading }) => {
  const colorClass = sectorColorClasses[sector.color_classification];
  const tradingSignal = tradingSignalDisplay[sector.trading_signal as keyof typeof tradingSignalDisplay];
  const sectorName = sectorDisplayNames[sector.sector as keyof typeof sectorDisplayNames] || sector.sector;

  // Get timeframe color indicators
  const getTimeframeColor = (score: number) => {
    if (score > 0.3) return '🟢';
    if (score > 0) return '🟡';
    if (score > -0.3) return '🔵';
    return '🔴';
  };

  // Format percentage
  const formatPercent = (value: number) => {
    const percent = value * 100;
    const sign = percent >= 0 ? '+' : '';
    return `${sign}${percent.toFixed(1)}%`;
  };

  return (
    <div
      className={`
        ${colorClass}
        border-2 rounded-lg p-4 cursor-pointer transition-all duration-200
        hover:scale-105 hover:shadow-lg
        ${isLoading ? 'opacity-50 animate-pulse' : ''}
      `}
      onClick={() => !isLoading && onClick(sector.sector)}
    >
      {/* Header */}
      <div className="flex justify-between items-start mb-3">
        <div>
          <h3 className="text-lg font-bold mb-1">{sectorName}</h3>
          <div className="flex items-center space-x-2">
            <span className={`text-sm font-medium ${tradingSignal?.color}`}>
              {tradingSignal?.icon} {tradingSignal?.text}
            </span>
          </div>
        </div>
        <div className="text-right">
          <div className="text-xl font-bold">
            {formatPercent(sector.sentiment_score)}
          </div>
          <div className="text-xs opacity-80">
            Confidence: {Math.round(sector.confidence_level * 100)}%
          </div>
        </div>
      </div>

      {/* Multi-timeframe indicators */}
      <div className="grid grid-cols-2 gap-2 mb-3 text-xs">
        <div className="flex justify-between">
          <span>30M:</span>
          <span className="font-mono">
            {getTimeframeColor(sector.timeframe_scores['30min'])} {formatPercent(sector.timeframe_scores['30min'])}
          </span>
        </div>
        <div className="flex justify-between">
          <span>1D:</span>
          <span className="font-mono">
            {getTimeframeColor(sector.timeframe_scores['1day'])} {formatPercent(sector.timeframe_scores['1day'])}
          </span>
        </div>
        <div className="flex justify-between">
          <span>3D:</span>
          <span className="font-mono">
            {getTimeframeColor(sector.timeframe_scores['3day'])} {formatPercent(sector.timeframe_scores['3day'])}
          </span>
        </div>
        <div className="flex justify-between">
          <span>1W:</span>
          <span className="font-mono">
            {getTimeframeColor(sector.timeframe_scores['1week'])} {formatPercent(sector.timeframe_scores['1week'])}
          </span>
        </div>
      </div>

      {/* Top stocks preview */}
      <div className="border-t border-white/20 pt-2">
        {sector.sentiment_score > 0 ? (
          // Show bullish stocks for positive sentiment
          <div>
            <div className="flex items-center mb-1">
              <TrendingUpIcon className="w-3 h-3 mr-1" />
              <span className="text-xs font-medium">TOP BULLISH:</span>
            </div>
            <div className="text-xs space-y-1">
              {sector.top_bullish?.slice(0, 3).map((stock, index) => (
                <div key={stock.symbol} className="flex justify-between">
                  <span className="font-mono">{stock.symbol}</span>
                  <span className="font-mono">{formatPercent(stock.change_percent / 100)}</span>
                </div>
              )) || (
                <div className="text-white/70 italic">No bullish stocks</div>
              )}
            </div>
          </div>
        ) : sector.sentiment_score < 0 ? (
          // Show bearish stocks for negative sentiment
          <div>
            <div className="flex items-center mb-1">
              <TrendingDownIcon className="w-3 h-3 mr-1" />
              <span className="text-xs font-medium">TOP BEARISH:</span>
            </div>
            <div className="text-xs space-y-1">
              {sector.top_bearish?.slice(0, 3).map((stock, index) => (
                <div key={stock.symbol} className="flex justify-between">
                  <span className="font-mono">{stock.symbol}</span>
                  <span className="font-mono">{formatPercent(stock.change_percent / 100)}</span>
                </div>
              )) || (
                <div className="text-white/70 italic">No bearish stocks</div>
              )}
            </div>
          </div>
        ) : (
          // Show mixed for neutral sentiment
          <div>
            <div className="text-xs font-medium mb-1">MIXED SIGNALS</div>
            <div className="text-xs text-white/70 italic">
              {sector.stock_count} stocks tracked
            </div>
          </div>
        )}
      </div>

      {/* Click indicator */}
      <div className="flex justify-end mt-2">
        <ChevronRightIcon className="w-4 h-4 opacity-60" />
      </div>
    </div>
  );
};

const SectorGrid: React.FC<SectorGridProps> = ({
  onSectorClick = () => {},
}) => {
  const [displaySectors, setDisplaySectors] = useState<SectorData[]>(defaultSectors);
  const [isLoading, setIsLoading] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);

  // Fetch sector data from API
  const fetchSectorData = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/sectors');
      if (response.ok) {
        const data = await response.json();
        
        // Backend returns sectors as an object, convert to array
        if (data.sectors && typeof data.sectors === 'object') {
          const sectorsArray = Object.values(data.sectors) as SectorData[];
          setDisplaySectors(sectorsArray);
        } else {
          setDisplaySectors(defaultSectors);
        }
        
        setLastUpdated(new Date().toISOString());
      } else {
        console.error('Failed to fetch sector data');
        setDisplaySectors(defaultSectors);
      }
    } catch (error) {
      console.error('Error fetching sector data:', error);
      setDisplaySectors(defaultSectors);
    } finally {
      setIsLoading(false);
    }
  };

  // Load data on component mount
  useEffect(() => {
    fetchSectorData();
  }, []);

  // Handle refresh button click
  const handleRefresh = () => {
    fetchSectorData();
  };

  const formatLastUpdated = (timestamp?: string | null) => {
    if (!timestamp) return 'Never';
    
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    
    return date.toLocaleDateString();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Market Sector Sentiment
          </h1>
          <p className="text-gray-600 mt-1">
            Real-time sector analysis for small-cap trading opportunities
          </p>
        </div>
        
        <div className="flex items-center space-x-4">
          <div className="text-sm text-gray-500">
            Last updated: {formatLastUpdated(lastUpdated)}
          </div>
          <button
            onClick={handleRefresh}
            disabled={isLoading}
            className={`
              flex items-center space-x-2 px-4 py-2 rounded-lg border
              transition-all duration-200
              ${isLoading
                ? 'bg-gray-100 text-gray-400 border-gray-200 cursor-not-allowed'
                : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50 hover:border-gray-400'
              }
            `}
          >
            <RefreshCwIcon className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
            <span>{isLoading ? 'Refreshing...' : 'Refresh'}</span>
          </button>
        </div>
      </div>

      {/* Sector Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {displaySectors.map((sector) => (
          <SectorCard
            key={sector.sector}
            sector={sector}
            onClick={onSectorClick}
            isLoading={isLoading}
          />
        ))}
      </div>

      {/* Performance Note */}
      <div className="text-center text-sm text-gray-500">
        <p>
          Monitoring {displaySectors.reduce((total, sector) => total + sector.stock_count, 0)} small-cap stocks 
          across 8 sectors for gap opportunities and sentiment analysis.
        </p>
      </div>
    </div>
  );
};

export default SectorGrid; 