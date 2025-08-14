/**
 * Sector Grid Component - Slice 1A Implementation
 * Color-coded 12-slot dashboard grid (11 FMP sectors + 1 theme)
 * Displays sentiment, top stocks, and trading signals
 */
'use client';

import React, { useState, useEffect, useRef } from 'react';
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

// Sector display names (FMP 11-sector taxonomy)
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

// Default sectors for loading state (11 sectors)
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
  'utilities',
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

  // Get timeframe color indicators (normalized thresholds)
  // Uses tight bands: [-1.0%, -0.3%, +0.3%, +1.0%]
  const getDotClass = (score: number) => {
    if (score >= 0.01) return 'bg-green-500';
    if (score >= 0.003) return 'bg-yellow-400';
    if (score > -0.003) return 'bg-blue-500';
    if (score > -0.01) return 'bg-orange-400';
    return 'bg-red-500';
  };

  const Dot: React.FC<{ value: number }> = ({ value }) => (
    <span className={`inline-block w-2 h-2 rounded-full mr-1 ${getDotClass(value)}`} />
  );

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
          <span className="font-mono flex items-center">
            <Dot value={sector.timeframe_scores['30min']} /> {formatPercent(sector.timeframe_scores['30min'])}
          </span>
        </div>
        <div className="flex justify-between">
          <span>1D:</span>
          <span className="font-mono flex items-center">
            <Dot value={sector.timeframe_scores['1day']} /> {formatPercent(sector.timeframe_scores['1day'])}
          </span>
        </div>
        <div className="flex justify-between">
          <span>3D:</span>
          <span className="font-mono flex items-center">
            <Dot value={sector.timeframe_scores['3day']} /> {formatPercent(sector.timeframe_scores['3day'])}
          </span>
        </div>
        <div className="flex justify-between">
          <span>1W:</span>
          <span className="font-mono flex items-center">
            <Dot value={sector.timeframe_scores['1week']} /> {formatPercent(sector.timeframe_scores['1week'])}
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
  const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
  const [displaySectors, setDisplaySectors] = useState<SectorData[]>([...defaultSectors, defaultThemeCard]);
  const [isLoading, setIsLoading] = useState(false); // initial data load/skeleton state
  const [isRefreshing, setIsRefreshing] = useState(false); // user-initiated refresh state
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);
  const [calcMode, setCalcMode] = useState<'simple' | 'weighted'>('simple');
  const [lastBatchTs, setLastBatchTs] = useState<string | null>(null);
  const [lastBatchTs3d, setLastBatchTs3d] = useState<string | null>(null);
  const [refreshMsg, setRefreshMsg] = useState<string | null>(null);
  const [threeDaySimple, setThreeDaySimple] = useState<Record<string, number>>({});
  const [threeDayWeighted, setThreeDayWeighted] = useState<Record<string, number>>({});
  const [oneWeekSimple, setOneWeekSimple] = useState<Record<string, number>>({});
  const [oneWeekWeighted, setOneWeekWeighted] = useState<Record<string, number>>({});
  const last3DFetchRef = useRef<number>(0);
  const last1WFetchRef = useRef<number>(0);
  const last30mFetchRef = useRef<number>(0);
  const [thirtyMinSimple, setThirtyMinSimple] = useState<Record<string, number>>({});
  const [thirtyMinWeighted, setThirtyMinWeighted] = useState<Record<string, number>>({});

  const apply3DToDisplay = () => {
    const map = calcMode === 'weighted' ? threeDayWeighted : threeDaySimple;
    if (!map || Object.keys(map).length === 0) return;
    setDisplaySectors(prev => prev.map(item => {
      const n = map[item.sector];
      if (typeof n === 'number') {
        return {
          ...item,
          timeframe_scores: { ...item.timeframe_scores, '3day': n },
        };
      }
      return item;
    }));
  };

  const apply1WToDisplay = () => {
    const map = calcMode === 'weighted' ? oneWeekWeighted : oneWeekSimple;
    if (!map || Object.keys(map).length === 0) return;
    setDisplaySectors(prev => prev.map(item => {
      const n = map[item.sector];
      if (typeof n === 'number') {
        return {
          ...item,
          timeframe_scores: { ...item.timeframe_scores, '1week': n },
        };
      }
      return item;
    }));
  };

  // Small helper to fetch with timeout
  const fetchWithTimeout = async (url: string, options: RequestInit = {}, timeoutMs = 10000): Promise<Response> => {
    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), timeoutMs);
    try {
      const resp = await fetch(url, { ...options, signal: controller.signal });
      return resp;
    } finally {
      clearTimeout(id);
    }
  };

  // Fetch sector data from API
  const fetchSectorData = async (fromRefresh: boolean = false) => {
    if (fromRefresh) {
      setIsRefreshing(true);
    } else {
      setIsLoading(true);
    }
    try {
      const baseUrl = `${API_BASE}/api/sectors/1day/`;
      const url = calcMode === 'weighted' ? `${baseUrl}?calc=weighted` : baseUrl;
      const response = await fetchWithTimeout(url, { cache: 'no-store' }, 10000);
      if (response.ok) {
        const data = await response.json();

        const raw = data.sectors;
        const arr: any[] = Array.isArray(raw)
          ? raw
          : (raw && typeof raw === 'object' ? Object.values(raw) : []);

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

        const normalized: SectorData[] = arr
          .filter((s: any) => allowed.has(String(s?.sector ?? '').toLowerCase()))
          .map((s: any) => {
            const norm = typeof s.sentiment_normalized === 'number'
              ? s.sentiment_normalized
              : (typeof s.sentiment_score === 'number' ? s.sentiment_score / 100.0 : 0);

            const colorFromNorm = (n: number) => {
              if (n <= -0.01) return 'dark_red';
              if (n <= -0.003) return 'light_red';
              if (n < 0.003) return 'blue_neutral';
              if (n < 0.01) return 'light_green';
              return 'dark_green';
            };

            const base: SectorData = {
              sector: s.sector,
              sentiment_score: norm,
              sentiment_normalized: norm,
              color_classification: (s.color_classification ?? colorFromNorm(norm)) as SectorData['color_classification'],
              trading_signal: s.trading_signal ?? 'NEUTRAL_CAUTIOUS',
              confidence_level: 0.0,
              timeframe_scores: { '30min': 0, '1day': norm, '3day': 0, '1week': 0 },
              stock_count: s.stock_count ?? 0,
              last_updated: s.timestamp ?? new Date().toISOString(),
              top_bullish: [],
              top_bearish: [],
            } as SectorData;
            const maybe30m = (calcMode === 'weighted' ? thirtyMinWeighted : thirtyMinSimple)[s.sector];
            if (typeof maybe30m === 'number') {
              base.timeframe_scores['30min'] = maybe30m;
            }
            // If we already have cached 3D/1W values, apply them without refetch
            const maybe3d = (calcMode === 'weighted' ? threeDayWeighted : threeDaySimple)[s.sector];
            if (typeof maybe3d === 'number') {
              base.timeframe_scores['3day'] = maybe3d;
            }
            const maybe1w = (calcMode === 'weighted' ? oneWeekWeighted : oneWeekSimple)[s.sector];
            if (typeof maybe1w === 'number') {
              base.timeframe_scores['1week'] = maybe1w;
            }
            return base;
          });

        setDisplaySectors([...normalized, defaultThemeCard]);
        const metaTs = data?.metadata?.timestamp as string | undefined;
        const ts = metaTs ?? new Date().toISOString();
        setLastUpdated(ts);
        // Only update lastBatchTs when reading from persisted simple endpoint
        if (calcMode === 'simple') {
          setLastBatchTs(ts);
        }
      } else {
        console.error('Failed to fetch sector data');
        setDisplaySectors([...defaultSectors, defaultThemeCard]);
      }
    } catch (error) {
      console.error('Error fetching sector data:', error);
      setDisplaySectors([...defaultSectors, defaultThemeCard]);
    } finally {
      if (fromRefresh) {
        setIsRefreshing(false);
      } else {
        setIsLoading(false);
      }
    }
  };

  const fetch3DData = async (force: boolean = false) => {
    const now = Date.now();
    if (!force && now - last3DFetchRef.current < 15000) return;
    try {
      const url3dBase = `${API_BASE}/api/sectors/3day/`;
      const resp3d = await fetchWithTimeout(url3dBase, { cache: 'no-store' }, 10000);
      if (resp3d.ok) {
        const data3d = await resp3d.json();
        const list3d: any[] = Array.isArray(data3d?.sectors)
          ? data3d.sectors
          : (data3d?.sectors && typeof data3d.sectors === 'object' ? Object.values(data3d.sectors) : []);
        const simple: Record<string, number> = {};
        const weighted: Record<string, number> = {};
        for (const s of list3d) {
          const nSimple = (typeof s?.sentiment_normalized === 'number')
            ? s.sentiment_normalized
            : (typeof s?.sentiment_score === 'number' ? s.sentiment_score / 100.0 : 0);
          const nWeighted = (typeof s?.sentiment_normalized_weighted === 'number')
            ? s.sentiment_normalized_weighted
            : (typeof s?.weighted_sentiment_score === 'number' ? s.weighted_sentiment_score / 100.0 : nSimple);
          if (s?.sector) {
            simple[String(s.sector)] = nSimple;
            weighted[String(s.sector)] = nWeighted;
          }
        }
        setThreeDaySimple(simple);
        setThreeDayWeighted(weighted);
        const meta3dTs = (data3d?.metadata?.timestamp as string | undefined) || null;
        if (meta3dTs) setLastBatchTs3d(meta3dTs);
        last3DFetchRef.current = now;
        // Apply to current display based on toggle
        apply3DToDisplay();
      }
    } catch (e) {
      console.warn('3D fetch skipped or failed', e);
    }
  };

  const fetch1WData = async (force: boolean = false) => {
    const now = Date.now();
    if (!force && now - last1WFetchRef.current < 15000) return;
    try {
      const url1w = `${API_BASE}/api/sectors/1week/`;
      const resp = await fetchWithTimeout(url1w, { cache: 'no-store' }, 10000);
      if (resp.ok) {
        const data = await resp.json();
        const list: any[] = Array.isArray(data?.sectors)
          ? data.sectors
          : (data?.sectors && typeof data.sectors === 'object' ? Object.values(data.sectors) : []);
        const simple: Record<string, number> = {};
        const weighted: Record<string, number> = {};
        for (const s of list) {
          const nSimple = (typeof s?.sentiment_normalized === 'number')
            ? s.sentiment_normalized
            : (typeof s?.sentiment_score === 'number' ? s.sentiment_score / 100.0 : 0);
          const nWeighted = (typeof s?.sentiment_normalized_weighted === 'number')
            ? s.sentiment_normalized_weighted
            : (typeof s?.weighted_sentiment_score === 'number' ? s.weighted_sentiment_score / 100.0 : nSimple);
          if (s?.sector) {
            simple[String(s.sector)] = nSimple;
            weighted[String(s.sector)] = nWeighted;
          }
        }
        setOneWeekSimple(simple);
        setOneWeekWeighted(weighted);
        last1WFetchRef.current = now;
        apply1WToDisplay();
      }
    } catch (e) {
      console.warn('1W fetch skipped or failed', e);
    }
  };

  const fetch30MData = async (force: boolean = false) => {
    const now = Date.now();
    if (!force && now - last30mFetchRef.current < 15000) return;
    try {
      const url = `${API_BASE}/api/sectors/30min/`;
      const resp = await fetchWithTimeout(url, { cache: 'no-store' }, 10000);
      if (resp.ok) {
        const data = await resp.json();
        const list: any[] = Array.isArray(data?.sectors)
          ? data.sectors
          : (data?.sectors && typeof data.sectors === 'object' ? Object.values(data.sectors) : []);
        const simple: Record<string, number> = {};
        const weighted: Record<string, number> = {};
        for (const s of list) {
          const nSimple = (typeof s?.sentiment_normalized === 'number')
            ? s.sentiment_normalized
            : (typeof s?.sentiment_score === 'number' ? s.sentiment_score / 100.0 : 0);
          const nWeighted = (typeof s?.sentiment_normalized_weighted === 'number')
            ? s.sentiment_normalized_weighted
            : (typeof s?.weighted_sentiment_score === 'number' ? s.weighted_sentiment_score / 100.0 : nSimple);
          if (s?.sector) {
            simple[String(s.sector)] = nSimple;
            weighted[String(s.sector)] = nWeighted;
          }
        }
        // Cache latest maps so toggling doesn't wipe 30M
        setThirtyMinSimple(simple);
        setThirtyMinWeighted(weighted);
        // Apply to display from cache
        setDisplaySectors(prev => prev.map(item => {
          const map = calcMode === 'weighted' ? weighted : simple;
          const n = map[item.sector];
          if (typeof n === 'number') {
            return { ...item, timeframe_scores: { ...item.timeframe_scores, '30min': n } };
          }
          return item;
        }));
        last30mFetchRef.current = now;
      }
    } catch (e) {
      console.warn('30M fetch skipped or failed', e);
    }
  };

  // Load data on component mount
  useEffect(() => {
    fetchSectorData(false);
    fetch3DData(true); // initial 3D load
    fetch1WData(true); // initial 1W load
    fetch30MData(true); // initial 30M load
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // When user toggles simple/weighted, refetch 1D preview and refresh 30M
  useEffect(() => {
    fetchSectorData(false);
    fetch30MData(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [calcMode]);

  // When toggle changes, reapply 3D from cached maps without refetching
  useEffect(() => {
    apply3DToDisplay();
    apply1WToDisplay();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [calcMode, threeDaySimple, threeDayWeighted, oneWeekSimple, oneWeekWeighted]);

  // Poll for a new persisted batch (checks simple endpoint regardless of toggle)
  const pollUntilNewBatch = async (prevTs: string | null, maxTries = 10, intervalMs = 3000): Promise<boolean> => {
    const baseUrl = `${API_BASE}/api/sectors/1day/`;
    for (let i = 0; i < maxTries; i++) {
      try {
        const resp = await fetchWithTimeout(baseUrl, { cache: 'no-store' }, 10000);
        if (resp.ok) {
          const data = await resp.json();
          const metaTs = (data?.metadata?.timestamp as string | undefined) || null;
          if (metaTs && metaTs !== prevTs) {
            setLastBatchTs(metaTs);
            return true;
          }
        }
      } catch {
        // ignore transient errors during polling
      }
      await new Promise((r) => setTimeout(r, intervalMs));
    }
    return false;
  };

  // 3D is close-to-close; no recompute from UI. We keep lastBatchTs3d for display only.

  // Handle refresh button click: POST recompute then poll until a new batch is persisted
  const handleRefresh = async () => {
    if (isRefreshing) return;
    setRefreshMsg('Scheduling recompute...');

    const recomputeUrl1d = `${API_BASE}/api/sectors/1day/recompute`;
    const headers: HeadersInit = { 'Content-Type': 'application/json', accept: 'application/json' };
    const adminToken = process.env.NEXT_PUBLIC_ADMIN_RECOMPUTE_TOKEN;
    if (adminToken) headers['X-Admin-Token'] = adminToken as string;

    const prevTs = lastBatchTs;
    const prevTs3d = lastBatchTs3d;

    try {
      // Only 1D recompute from UI. 3D is close-to-close (read-only here).
      const r1 = await fetchWithTimeout(recomputeUrl1d, { method: 'POST', headers }, 10000);

      if (r1.status === 403) {
        setRefreshMsg('Recompute disabled by server settings.');
        fetchSectorData(false);
        return;
      }
      if (r1.status === 401) {
        setRefreshMsg('Unauthorized. Missing or invalid admin token.');
        fetchSectorData(false);
        return;
      }
      if (r1.status === 429) {
        setRefreshMsg('Cooldown active. Try again shortly.');
        return;
      }
      if (r1.status === 409) {
        setRefreshMsg('Recompute already in progress...');
      } else if (r1.status === 202) {
        setRefreshMsg('Updating in background...');
      } else {
        setRefreshMsg('Polling for 1D updates...');
      }

      // Background poll for a new persisted timestamp (non-blocking UI)
      pollUntilNewBatch(prevTs, 10, 3000).then(async (gotNew1d) => {
        if (gotNew1d) {
          setRefreshMsg(null);
          // Refresh 1D according to current toggle and update 30M once; leave 3D/1W unchanged
          await fetchSectorData(false);
          await fetch30MData(true);
        } else {
          setRefreshMsg('No update detected.');
          // Light refresh of current view
          fetchSectorData(false);
        }
      });
    } catch (err) {
      console.error('Error scheduling recompute:', err);
      setRefreshMsg('Error scheduling recompute.');
      fetchSectorData(false);
    } finally {
      setIsRefreshing(false);
    }
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
          {/* Calculation mode toggle */}
          <div className="hidden md:flex items-center bg-gray-200 rounded-full p-1 shadow-inner">
            <button
              type="button"
              onClick={() => setCalcMode('simple')}
              className={`px-3 py-1 text-sm rounded-full transition ${
                calcMode === 'simple' ? 'bg-white shadow text-gray-900' : 'text-gray-600 hover:text-gray-800'
              }`}
              title="Use persisted simple average (stable)"
            >
              Simple
            </button>
            <button
              type="button"
              onClick={() => setCalcMode('weighted')}
              className={`px-3 py-1 text-sm rounded-full transition flex items-center space-x-1 ${
                calcMode === 'weighted' ? 'bg-white shadow text-gray-900' : 'text-gray-600 hover:text-gray-800'
              }`}
              title="Preview dollar-volume weighted (on-the-fly)"
            >
              <span>Weighted</span>
              <span className="ml-1 inline-block text-[10px] px-1.5 py-0.5 rounded-full bg-indigo-100 text-indigo-700 border border-indigo-200">Preview</span>
            </button>
          </div>

          <div className="text-sm text-gray-500 text-right">
            <div>Last updated: {formatLastUpdated(lastUpdated)}</div>
            {refreshMsg && (
              <div className="text-[11px] text-gray-500">{refreshMsg}</div>
            )}
          </div>
          <button
            onClick={handleRefresh}
            disabled={isRefreshing}
            className={`
              flex items-center space-x-2 px-4 py-2 rounded-lg border
              transition-all duration-200
              ${isRefreshing
                ? 'bg-gray-100 text-gray-400 border-gray-200 cursor-not-allowed'
                : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50 hover:border-gray-400'
              }
            `}
          >
            <RefreshCwIcon className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
            <span>{isRefreshing ? 'Refreshing...' : 'Refresh'}</span>
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