/**
 * Sector Grid Component - Slice 1A Implementation
 * Color-coded 12-slot dashboard grid (11 sectors + 1 theme placeholder)
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
  sentiment_score: number; // normalized [-1,1] for UI
  sentiment_normalized?: number;
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

type CalcMode = 'simple' | 'weighted';

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
const sectorDisplayNames: Record<string, string> = {
  'basic_materials': 'Basic Materials',
  'communication_services': 'Communication Services',
  'consumer_cyclical': 'Consumer Cyclical',
  'consumer_defensive': 'Consumer Defensive',
  'energy': 'Energy',
  'financial_services': 'Financial Services',
  'healthcare': 'Healthcare',
  'industrials': 'Industrials',
  'real_estate': 'Real Estate',
  'technology': 'Technology',
  'utilities': 'Utilities',
  'theme_slot': 'Theme'
};

// Default sectors (11) + theme placeholder
const makeDefaultSector = (sector: string): SectorData => ({
  sector,
  sentiment_score: 0.0,
  color_classification: 'blue_neutral',
  confidence_level: 0.0,
  stock_count: 0,
  trading_signal: 'NEUTRAL_CAUTIOUS',
  timeframe_scores: { '30min': 0, '1day': 0, '3day': 0, '1week': 0 },
  last_updated: new Date().toISOString(),
  top_bullish: [],
  top_bearish: []
});

const defaultSectors: SectorData[] = [
  'basic_materials',
  'communication_services',
  'consumer_cyclical',
  'consumer_defensive',
  'energy',
  'financial_services',
  'healthcare',
  'industrials',
  'real_estate',
  'technology',
  'utilities'
].map(makeDefaultSector);

const defaultThemeCard: SectorData = makeDefaultSector('theme_slot');

const SectorCard: React.FC<{
  sector: SectorData;
  onClick: (sector: string) => void;
  isLoading: boolean;
}> = ({ sector, onClick, isLoading }) => {
  const colorClass = sectorColorClasses[sector.color_classification];
  const tradingSignal = tradingSignalDisplay[sector.trading_signal as keyof typeof tradingSignalDisplay];
  const sectorName = sectorDisplayNames[sector.sector as keyof typeof sectorDisplayNames] || sector.sector;

  // Get timeframe color class for Tailwind dot (normalized [-1,1])
  // Tighter small-cap 1D color bands (normalized):
  // red ≤ -0.01, light_red -0.01..-0.003, neutral -0.003..0.003, light_green 0.003..0.01, green ≥ 0.01
  const getTimeframeClass = (score: number) => {
    if (score >= 0.01) return 'bg-green-500';
    if (score >= 0.003) return 'bg-yellow-400';
    if (score > -0.003) return 'bg-blue-500';
    if (score > -0.01) return 'bg-orange-400';
    return 'bg-red-500';
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
        <div className="flex justify-between items-center">
          <span>30M:</span>
          <span className="font-mono flex items-center">
            <span className={`inline-block w-2.5 h-2.5 rounded-full mr-1 ${getTimeframeClass(sector.timeframe_scores['30min'])}`} />
            {formatPercent(sector.timeframe_scores['30min'])}
          </span>
        </div>
        <div className="flex justify-between items-center">
          <span>1D:</span>
          <span className="font-mono flex items-center">
            <span className={`inline-block w-2.5 h-2.5 rounded-full mr-1 ${getTimeframeClass(sector.timeframe_scores['1day'])}`} />
            {formatPercent(sector.timeframe_scores['1day'])}
          </span>
        </div>
        <div className="flex justify-between items-center">
          <span>3D:</span>
          <span className="font-mono flex items-center">
            <span className={`inline-block w-2.5 h-2.5 rounded-full mr-1 ${getTimeframeClass(sector.timeframe_scores['3day'])}`} />
            {formatPercent(sector.timeframe_scores['3day'])}
          </span>
        </div>
        <div className="flex justify-between items-center">
          <span>1W:</span>
          <span className="font-mono flex items-center">
            <span className={`inline-block w-2.5 h-2.5 rounded-full mr-1 ${getTimeframeClass(sector.timeframe_scores['1week'])}`} />
            {formatPercent(sector.timeframe_scores['1week'])}
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
  const [displaySectors, setDisplaySectors] = useState<SectorData[]>([...defaultSectors, defaultThemeCard]);
  const [isLoading, setIsLoading] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);
  const [calcMode, setCalcMode] = useState<CalcMode>('simple');
  const [lastBatchTimestamp, setLastBatchTimestamp] = useState<string | null>(null);

  // Fetch sector data from API
  const fetchSectorData = async () => {
    setIsLoading(true);
    try {
      const baseUrl = 'http://localhost:8000/api/sectors/1day/';
      const url = calcMode === 'weighted' ? `${baseUrl}?calc=weighted` : baseUrl;
      const response = await fetch(url);
      if (response.ok) {
        const data = await response.json();
        const raw = data.sectors;
        const arr: any[] = Array.isArray(raw) ? raw : (raw && typeof raw === 'object' ? Object.values(raw) : []);
        const allowed = new Set([
          'basic_materials',
          'communication_services',
          'consumer_cyclical',
          'consumer_defensive',
          'energy',
          'financial_services',
          'healthcare',
          'industrials',
          'real_estate',
          'technology',
          'utilities',
        ]);
        const filtered = arr.filter((s: any) => allowed.has(String(s?.sector ?? '').toLowerCase()));
        const normalized: SectorData[] = filtered.map((s: any) => {
          const norm = typeof s.sentiment_normalized === 'number'
            ? s.sentiment_normalized
            : (typeof s.sentiment_score === 'number' ? s.sentiment_score / 100.0 : 0);
          return {
            sector: s.sector,
            sentiment_score: norm,
            sentiment_normalized: norm,
            color_classification: (s.color_classification ?? 'blue_neutral'),
            trading_signal: s.trading_signal ?? 'NEUTRAL_CAUTIOUS',
            confidence_level: 0.0,
            // Populate 1D row with the current normalized score; other timeframes pending
            timeframe_scores: { '30min': 0, '1day': norm, '3day': 0, '1week': 0 },
            stock_count: s.stock_count ?? 0,
            last_updated: s.timestamp ?? new Date().toISOString(),
            top_bullish: [],
            top_bearish: []
          } as SectorData;
        });
        setDisplaySectors([...normalized, defaultThemeCard]);
        setLastUpdated(new Date().toISOString());
        const metaTs = data?.metadata?.timestamp as string | undefined;
        if (metaTs) setLastBatchTimestamp(metaTs);
      } else {
        console.error('Failed to fetch sector data');
        setDisplaySectors([...defaultSectors, defaultThemeCard]);
      }
    } catch (error) {
      console.error('Error fetching sector data:', error);
      setDisplaySectors([...defaultSectors, defaultThemeCard]);
    } finally {
      setIsLoading(false);
    }
  };

  // Load data on component mount
  useEffect(() => {
    fetchSectorData();
  }, [calcMode]);

  // Handle refresh button click
  const postRecompute = async (): Promise<boolean> => {
    try {
      const token = typeof window !== 'undefined' ? window.localStorage.getItem('adminToken') : null;
      const resp = await fetch('http://localhost:8000/api/sectors/1day/recompute', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'X-Admin-Token': token } : {})
        }
      });
      if (resp.status === 202 || resp.ok) return true;
      console.warn('Recompute request rejected', await resp.text());
      return false;
    } catch (e) {
      console.error('Recompute request failed', e);
      return false;
    }
  };

  const pollUntilNewBatch = async (prevTs: string | null, timeoutMs = 60000, intervalMs = 2000) => {
    const start = Date.now();
    while (Date.now() - start < timeoutMs) {
      try {
        const resp = await fetch('http://localhost:8000/api/sectors/1day/');
        if (resp.ok) {
          const data = await resp.json();
          const metaTs = data?.metadata?.timestamp as string | undefined;
          if (metaTs && metaTs !== prevTs) {
            // Update UI with fresh data
            const raw = data.sectors;
            const arr: any[] = Array.isArray(raw) ? raw : (raw && typeof raw === 'object' ? Object.values(raw) : []);
            const allowed = new Set([
              'basic_materials','communication_services','consumer_cyclical','consumer_defensive','energy','financial_services','healthcare','industrials','real_estate','technology','utilities',
            ]);
            const filtered = arr.filter((s: any) => allowed.has(String(s?.sector ?? '').toLowerCase()));
            const normalized: SectorData[] = filtered.map((s: any) => {
              const norm = typeof s.sentiment_normalized === 'number' ? s.sentiment_normalized : (typeof s.sentiment_score === 'number' ? s.sentiment_score / 100.0 : 0);
              return {
                sector: s.sector,
                sentiment_score: norm,
                sentiment_normalized: norm,
                color_classification: (s.color_classification ?? 'blue_neutral'),
                trading_signal: s.trading_signal ?? 'NEUTRAL_CAUTIOUS',
                confidence_level: 0.0,
                timeframe_scores: { '30min': 0, '1day': norm, '3day': 0, '1week': 0 },
                stock_count: s.stock_count ?? 0,
                last_updated: s.timestamp ?? new Date().toISOString(),
                top_bullish: [],
                top_bearish: []
              } as SectorData;
            });
            setDisplaySectors([...normalized, defaultThemeCard]);
            setLastUpdated(new Date().toISOString());
            setLastBatchTimestamp(metaTs);
            return true;
          }
        }
      } catch (e) {
        // ignore and continue polling
      }
      await new Promise(r => setTimeout(r, intervalMs));
    }
    return false;
  };

  const handleRefresh = async () => {
    setIsLoading(true);
    const prevTs = lastBatchTimestamp;
    const accepted = await postRecompute();
    if (accepted) {
      await pollUntilNewBatch(prevTs);
    } else {
      // Fallback: just refetch current data
      await fetchSectorData();
    }
    setIsLoading(false);
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
          {/* Calc toggle */}
          <div className="flex items-center space-x-2 text-sm">
            <label className="text-gray-600">Calc:</label>
            <select
              value={calcMode}
              onChange={(e) => setCalcMode(e.target.value as CalcMode)}
              className="bg-white border border-gray-300 text-gray-700 rounded px-2 py-1"
            >
              <option value="simple">Simple (Persisted)</option>
              <option value="weighted">Weighted (Preview)</option>
            </select>
          </div>
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
          across 11 sectors (plus 1 theme) for gap opportunities and sentiment analysis.
        </p>
      </div>
    </div>
  );
};

export default SectorGrid; 