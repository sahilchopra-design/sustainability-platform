import React, { useEffect, useRef, useState, useCallback } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { 
  Map, Layers, Filter, X, ZoomIn, ZoomOut, 
  Maximize2, MapPin, AlertTriangle, Info
} from 'lucide-react';

// Set Mapbox token
mapboxgl.accessToken = process.env.REACT_APP_MAPBOX_TOKEN;

// Risk level color mapping
const RISK_COLORS = {
  critical: '#ef4444',  // Red
  high: '#f97316',      // Orange
  medium: '#eab308',    // Yellow
  low: '#22c55e',       // Green
  default: '#6b7280',   // Gray
};

// Asset type icons
const ASSET_TYPE_CONFIG = {
  reserve: { color: '#3b82f6', label: 'Reserves' },
  power_plant: { color: '#10b981', label: 'Power Plants' },
  infrastructure: { color: '#8b5cf6', label: 'Infrastructure' },
  nature_risk: { color: '#06b6d4', label: 'Nature Risk' },
  carbon: { color: '#84cc16', label: 'Carbon Projects' },
};

// Get risk category from score
const getRiskCategory = (score) => {
  if (score >= 0.75) return 'critical';
  if (score >= 0.5) return 'high';
  if (score >= 0.25) return 'medium';
  return 'low';
};

// Format currency
const formatCurrency = (value) => {
  if (!value) return 'N/A';
  if (value >= 1e9) return `$${(value / 1e9).toFixed(1)}B`;
  if (value >= 1e6) return `$${(value / 1e6).toFixed(1)}M`;
  return `$${value.toLocaleString()}`;
};

export function AssetMapViewer({ 
  assets = [], 
  title = "Asset Map",
  subtitle = "Geographic distribution of assets",
  onAssetClick,
  showFilters = true,
  showLegend = true,
  height = "500px",
  initialCenter = [0, 20],
  initialZoom = 1.5,
  module = "stranded-assets"
}) {
  const mapContainer = useRef(null);
  const map = useRef(null);
  const markersRef = useRef([]);
  const popupRef = useRef(null);
  
  const [mapLoaded, setMapLoaded] = useState(false);
  const [selectedAsset, setSelectedAsset] = useState(null);
  const [filters, setFilters] = useState({
    assetTypes: Object.keys(ASSET_TYPE_CONFIG),
    riskLevels: ['low', 'medium', 'high', 'critical'],
  });
  const [isFullscreen, setIsFullscreen] = useState(false);

  // Initialize map
  useEffect(() => {
    if (map.current) return;
    
    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: 'mapbox://styles/mapbox/dark-v11',
      center: initialCenter,
      zoom: initialZoom,
      attributionControl: false,
    });

    map.current.addControl(new mapboxgl.NavigationControl(), 'top-right');
    map.current.addControl(new mapboxgl.ScaleControl(), 'bottom-left');
    
    map.current.on('load', () => {
      setMapLoaded(true);
    });

    return () => {
      if (map.current) {
        map.current.remove();
        map.current = null;
      }
    };
  }, [initialCenter, initialZoom]);

  // Update markers when assets or filters change
  useEffect(() => {
    if (!mapLoaded || !map.current) return;

    // Clear existing markers
    markersRef.current.forEach(marker => marker.remove());
    markersRef.current = [];

    // Filter assets
    const filteredAssets = assets.filter(asset => {
      const riskCategory = getRiskCategory(asset.risk_score || 0);
      const assetType = asset.type || 'default';
      
      return filters.assetTypes.includes(assetType) && 
             filters.riskLevels.includes(riskCategory);
    });

    // Add markers for each asset
    filteredAssets.forEach(asset => {
      if (!asset.latitude || !asset.longitude) return;

      const riskCategory = getRiskCategory(asset.risk_score || 0);
      const riskColor = RISK_COLORS[riskCategory] || RISK_COLORS.default;
      const assetConfig = ASSET_TYPE_CONFIG[asset.type] || { color: '#6b7280', label: 'Asset' };

      // Create custom marker element
      const el = document.createElement('div');
      el.className = 'asset-marker';
      el.innerHTML = `
        <div style="
          width: 24px;
          height: 24px;
          border-radius: 50%;
          background: ${riskColor};
          border: 3px solid white;
          box-shadow: 0 2px 8px rgba(0,0,0,0.3);
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: transform 0.2s;
        ">
          <div style="
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: white;
          "></div>
        </div>
      `;

      // Add hover effect
      el.addEventListener('mouseenter', () => {
        el.firstChild.style.transform = 'scale(1.3)';
      });
      el.addEventListener('mouseleave', () => {
        el.firstChild.style.transform = 'scale(1)';
      });

      // Create popup
      const popup = new mapboxgl.Popup({
        offset: 25,
        closeButton: false,
        maxWidth: '300px',
      }).setHTML(`
        <div style="padding: 8px; font-family: system-ui, sans-serif;">
          <div style="font-weight: 600; font-size: 14px; margin-bottom: 4px;">${asset.name}</div>
          <div style="font-size: 12px; color: #6b7280; margin-bottom: 8px;">${asset.location || 'Unknown location'}</div>
          <div style="display: flex; gap: 8px; margin-bottom: 8px;">
            <span style="
              padding: 2px 8px;
              border-radius: 9999px;
              font-size: 11px;
              font-weight: 500;
              background: ${assetConfig.color}20;
              color: ${assetConfig.color};
            ">${assetConfig.label}</span>
            <span style="
              padding: 2px 8px;
              border-radius: 9999px;
              font-size: 11px;
              font-weight: 500;
              background: ${riskColor}20;
              color: ${riskColor};
            ">${riskCategory.toUpperCase()} RISK</span>
          </div>
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 4px; font-size: 12px;">
            <div style="color: #6b7280;">Risk Score:</div>
            <div style="font-weight: 500;">${((asset.risk_score || 0) * 100).toFixed(0)}%</div>
            ${asset.capacity ? `
              <div style="color: #6b7280;">Capacity:</div>
              <div style="font-weight: 500;">${asset.capacity}</div>
            ` : ''}
            ${asset.counterparty ? `
              <div style="color: #6b7280;">Counterparty:</div>
              <div style="font-weight: 500;">${asset.counterparty}</div>
            ` : ''}
          </div>
        </div>
      `);

      // Create marker
      const marker = new mapboxgl.Marker(el)
        .setLngLat([asset.longitude, asset.latitude])
        .setPopup(popup)
        .addTo(map.current);

      // Click handler
      el.addEventListener('click', () => {
        setSelectedAsset(asset);
        if (onAssetClick) onAssetClick(asset);
      });

      markersRef.current.push(marker);
    });

    // Fit bounds if there are assets
    if (filteredAssets.length > 0) {
      const bounds = new mapboxgl.LngLatBounds();
      filteredAssets.forEach(asset => {
        if (asset.latitude && asset.longitude) {
          bounds.extend([asset.longitude, asset.latitude]);
        }
      });
      
      if (!bounds.isEmpty()) {
        map.current.fitBounds(bounds, {
          padding: 50,
          maxZoom: 8,
          duration: 1000,
        });
      }
    }
  }, [assets, filters, mapLoaded, onAssetClick]);

  // Toggle filter
  const toggleAssetType = (type) => {
    setFilters(prev => ({
      ...prev,
      assetTypes: prev.assetTypes.includes(type)
        ? prev.assetTypes.filter(t => t !== type)
        : [...prev.assetTypes, type]
    }));
  };

  const toggleRiskLevel = (level) => {
    setFilters(prev => ({
      ...prev,
      riskLevels: prev.riskLevels.includes(level)
        ? prev.riskLevels.filter(l => l !== level)
        : [...prev.riskLevels, level]
    }));
  };

  // Zoom controls
  const handleZoomIn = () => map.current?.zoomIn();
  const handleZoomOut = () => map.current?.zoomOut();
  const handleResetView = () => {
    map.current?.flyTo({
      center: initialCenter,
      zoom: initialZoom,
      duration: 1000,
    });
  };

  // Calculate stats
  const filteredCount = assets.filter(asset => {
    const riskCategory = getRiskCategory(asset.risk_score || 0);
    return filters.assetTypes.includes(asset.type) && filters.riskLevels.includes(riskCategory);
  }).length;

  const riskStats = {
    critical: assets.filter(a => getRiskCategory(a.risk_score || 0) === 'critical').length,
    high: assets.filter(a => getRiskCategory(a.risk_score || 0) === 'high').length,
    medium: assets.filter(a => getRiskCategory(a.risk_score || 0) === 'medium').length,
    low: assets.filter(a => getRiskCategory(a.risk_score || 0) === 'low').length,
  };

  return (
    <Card className={`${isFullscreen ? 'fixed inset-4 z-50' : ''}`} data-testid="asset-map-viewer">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
              <Map className="h-5 w-5 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <CardTitle className="text-lg">{title}</CardTitle>
              <p className="text-sm text-slate-500">{subtitle}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="outline">{filteredCount} / {assets.length} assets</Badge>
            <button
              onClick={() => setIsFullscreen(!isFullscreen)}
              className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
            >
              {isFullscreen ? <X className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
            </button>
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="p-0">
        {/* Filters */}
        {showFilters && (
          <div className="px-4 py-3 border-b bg-slate-50 dark:bg-slate-800/50">
            <div className="flex flex-wrap items-center gap-4">
              {/* Asset Type Filters */}
              <div className="flex items-center gap-2">
                <Layers className="h-4 w-4 text-slate-400" />
                <span className="text-xs text-slate-500 mr-1">Type:</span>
                {Object.entries(ASSET_TYPE_CONFIG).map(([type, config]) => (
                  <button
                    key={type}
                    onClick={() => toggleAssetType(type)}
                    className={`px-2 py-1 rounded-full text-xs font-medium transition-all ${
                      filters.assetTypes.includes(type)
                        ? 'text-white shadow-sm'
                        : 'bg-slate-200 dark:bg-slate-700 text-slate-500'
                    }`}
                    style={filters.assetTypes.includes(type) ? { backgroundColor: config.color } : {}}
                  >
                    {config.label}
                  </button>
                ))}
              </div>

              {/* Risk Level Filters */}
              <div className="flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 text-slate-400" />
                <span className="text-xs text-slate-500 mr-1">Risk:</span>
                {Object.entries(RISK_COLORS).filter(([k]) => k !== 'default').map(([level, color]) => (
                  <button
                    key={level}
                    onClick={() => toggleRiskLevel(level)}
                    className={`px-2 py-1 rounded-full text-xs font-medium capitalize transition-all ${
                      filters.riskLevels.includes(level)
                        ? 'text-white shadow-sm'
                        : 'bg-slate-200 dark:bg-slate-700 text-slate-500'
                    }`}
                    style={filters.riskLevels.includes(level) ? { backgroundColor: color } : {}}
                  >
                    {level}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Map Container */}
        <div className="relative" style={{ height: isFullscreen ? 'calc(100vh - 200px)' : height }}>
          <div ref={mapContainer} className="absolute inset-0" />
          
          {/* Custom Zoom Controls */}
          <div className="absolute top-4 left-4 flex flex-col gap-1 bg-white dark:bg-slate-800 rounded-lg shadow-lg overflow-hidden">
            <button
              onClick={handleZoomIn}
              className="p-2 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
              title="Zoom In"
            >
              <ZoomIn className="h-4 w-4" />
            </button>
            <div className="h-px bg-slate-200 dark:bg-slate-700" />
            <button
              onClick={handleZoomOut}
              className="p-2 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
              title="Zoom Out"
            >
              <ZoomOut className="h-4 w-4" />
            </button>
            <div className="h-px bg-slate-200 dark:bg-slate-700" />
            <button
              onClick={handleResetView}
              className="p-2 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
              title="Reset View"
            >
              <MapPin className="h-4 w-4" />
            </button>
          </div>

          {/* Legend */}
          {showLegend && (
            <div className="absolute bottom-4 left-4 bg-white dark:bg-slate-800 rounded-lg shadow-lg p-3">
              <p className="text-xs font-medium text-slate-500 mb-2">Risk Level</p>
              <div className="space-y-1">
                {Object.entries(RISK_COLORS).filter(([k]) => k !== 'default').map(([level, color]) => (
                  <div key={level} className="flex items-center gap-2">
                    <div 
                      className="w-3 h-3 rounded-full" 
                      style={{ backgroundColor: color }}
                    />
                    <span className="text-xs capitalize">{level}</span>
                    <span className="text-xs text-slate-400">({riskStats[level]})</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Stats Panel */}
          <div className="absolute top-4 right-16 bg-white dark:bg-slate-800 rounded-lg shadow-lg p-3">
            <div className="grid grid-cols-2 gap-3 text-center">
              <div>
                <p className="text-lg font-bold text-red-500">{riskStats.critical + riskStats.high}</p>
                <p className="text-xs text-slate-500">High Risk</p>
              </div>
              <div>
                <p className="text-lg font-bold text-emerald-500">{riskStats.low + riskStats.medium}</p>
                <p className="text-xs text-slate-500">Lower Risk</p>
              </div>
            </div>
          </div>
        </div>

        {/* Selected Asset Detail */}
        {selectedAsset && (
          <div className="px-4 py-3 border-t bg-slate-50 dark:bg-slate-800/50">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div 
                  className="w-4 h-4 rounded-full"
                  style={{ backgroundColor: RISK_COLORS[getRiskCategory(selectedAsset.risk_score || 0)] }}
                />
                <div>
                  <p className="font-medium">{selectedAsset.name}</p>
                  <p className="text-xs text-slate-500">
                    {selectedAsset.location} • {selectedAsset.counterparty}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <div className="text-right">
                  <p className="text-xs text-slate-500">Risk Score</p>
                  <p className="font-bold">{((selectedAsset.risk_score || 0) * 100).toFixed(0)}%</p>
                </div>
                {selectedAsset.capacity && (
                  <div className="text-right">
                    <p className="text-xs text-slate-500">Capacity</p>
                    <p className="font-bold">{selectedAsset.capacity}</p>
                  </div>
                )}
                <button
                  onClick={() => setSelectedAsset(null)}
                  className="p-1 hover:bg-slate-200 dark:hover:bg-slate-700 rounded"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default AssetMapViewer;
