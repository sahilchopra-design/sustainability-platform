/**
 * Water Risk Map Component
 * Interactive Mapbox visualization for water stress locations
 */
import React, { useEffect, useRef, useState } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../../../components/ui/card';
import { Badge } from '../../../../components/ui/badge';
import { Button } from '../../../../components/ui/button';
import { Droplets, Layers, ZoomIn, ZoomOut, Locate, AlertTriangle } from 'lucide-react';
import { MapboxTokenGate } from '../../../../components/shared/MapboxTokenGate';

// Risk level colors
const getRiskColor = (riskLevel) => {
  if (riskLevel >= 4) return '#ef4444'; // red
  if (riskLevel >= 3) return '#f97316'; // orange
  if (riskLevel >= 2) return '#eab308'; // yellow
  if (riskLevel >= 1) return '#22c55e'; // green
  return '#3b82f6'; // blue (low)
};

const getRiskLabel = (riskLevel) => {
  if (riskLevel >= 4) return 'Extremely High';
  if (riskLevel >= 3) return 'High';
  if (riskLevel >= 2) return 'Medium';
  if (riskLevel >= 1) return 'Low-Medium';
  return 'Low';
};

function WaterRiskMapInner({ locations = [], onLocationSelect, selectedLocationId, accessToken }) {
  if (accessToken) mapboxgl.accessToken = accessToken;
  const mapContainer = useRef(null);
  const map = useRef(null);
  const markersRef = useRef([]);
  const [mapLoaded, setMapLoaded] = useState(false);
  const [mapStyle, setMapStyle] = useState('light');

  // Initialize map
  useEffect(() => {
    if (map.current) return;

    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: mapStyle === 'light' 
        ? 'mapbox://styles/mapbox/light-v11'
        : 'mapbox://styles/mapbox/dark-v11',
      center: [0, 20],
      zoom: 1.5,
      projection: 'mercator',
    });

    map.current.addControl(new mapboxgl.NavigationControl(), 'top-right');
    map.current.addControl(new mapboxgl.ScaleControl(), 'bottom-left');

    map.current.on('load', () => {
      setMapLoaded(true);
    });

    return () => {
      markersRef.current.forEach(marker => marker.remove());
      if (map.current) {
        map.current.remove();
        map.current = null;
      }
    };
  }, []);

  // Update map style
  useEffect(() => {
    if (!map.current || !mapLoaded) return;
    
    map.current.setStyle(
      mapStyle === 'light' 
        ? 'mapbox://styles/mapbox/light-v11'
        : 'mapbox://styles/mapbox/dark-v11'
    );
  }, [mapStyle, mapLoaded]);

  // Add markers for locations
  useEffect(() => {
    if (!map.current || !mapLoaded || !locations.length) return;

    // Clear existing markers
    markersRef.current.forEach(marker => marker.remove());
    markersRef.current = [];

    // Add new markers
    const bounds = new mapboxgl.LngLatBounds();

    locations.forEach(location => {
      const { longitude, latitude, name, water_stress, country_code, id } = location;
      
      if (!longitude || !latitude) return;

      const riskLevel = water_stress || 0;
      const color = getRiskColor(riskLevel);
      const isSelected = id === selectedLocationId;

      // Create marker element
      const el = document.createElement('div');
      el.className = 'water-risk-marker';
      el.style.cssText = `
        width: ${isSelected ? '28px' : '20px'};
        height: ${isSelected ? '28px' : '20px'};
        background-color: ${color};
        border: 3px solid ${isSelected ? '#fff' : 'rgba(255,255,255,0.8)'};
        border-radius: 50%;
        cursor: pointer;
        transition: all 0.2s ease;
        box-shadow: 0 2px 6px rgba(0,0,0,0.3);
        display: flex;
        align-items: center;
        justify-content: center;
      `;

      // Add pulse animation for high risk
      if (riskLevel >= 3) {
        el.innerHTML = `
          <div style="
            position: absolute;
            width: 100%;
            height: 100%;
            border-radius: 50%;
            background-color: ${color};
            opacity: 0.4;
            animation: pulse 2s infinite;
          "></div>
        `;
      }

      // Create popup
      const popup = new mapboxgl.Popup({
        offset: 25,
        closeButton: true,
        closeOnClick: false,
      }).setHTML(`
        <div style="padding: 8px; min-width: 200px;">
          <h3 style="font-weight: 600; margin-bottom: 8px; font-size: 14px;">${name}</h3>
          <div style="display: flex; flex-direction: column; gap: 4px; font-size: 12px;">
            <div style="display: flex; justify-content: space-between;">
              <span style="color: #64748b;">Country:</span>
              <span style="font-weight: 500;">${country_code}</span>
            </div>
            <div style="display: flex; justify-content: space-between;">
              <span style="color: #64748b;">Water Stress:</span>
              <span style="font-weight: 500; color: ${color};">${riskLevel.toFixed(1)} / 5</span>
            </div>
            <div style="display: flex; justify-content: space-between;">
              <span style="color: #64748b;">Risk Level:</span>
              <span style="font-weight: 500; color: ${color};">${getRiskLabel(riskLevel)}</span>
            </div>
          </div>
          <button 
            onclick="window.selectWaterLocation('${id}')"
            style="
              width: 100%;
              margin-top: 12px;
              padding: 6px 12px;
              background-color: #3b82f6;
              color: white;
              border: none;
              border-radius: 4px;
              cursor: pointer;
              font-size: 12px;
            "
          >
            View Full Analysis
          </button>
        </div>
      `);

      // Create marker
      const marker = new mapboxgl.Marker(el)
        .setLngLat([longitude, latitude])
        .setPopup(popup)
        .addTo(map.current);

      // Click handler
      el.addEventListener('click', () => {
        if (onLocationSelect) {
          onLocationSelect(id);
        }
      });

      markersRef.current.push(marker);
      bounds.extend([longitude, latitude]);
    });

    // Fit map to bounds
    if (locations.length > 1) {
      map.current.fitBounds(bounds, { padding: 50, maxZoom: 8 });
    } else if (locations.length === 1) {
      map.current.flyTo({
        center: [locations[0].longitude, locations[0].latitude],
        zoom: 6,
      });
    }

    // Global function for popup button
    window.selectWaterLocation = (id) => {
      if (onLocationSelect) onLocationSelect(id);
    };

    return () => {
      delete window.selectWaterLocation;
    };
  }, [locations, mapLoaded, selectedLocationId, onLocationSelect]);

  // Fly to selected location
  useEffect(() => {
    if (!map.current || !mapLoaded || !selectedLocationId) return;

    const location = locations.find(l => l.id === selectedLocationId);
    if (location && location.longitude && location.latitude) {
      map.current.flyTo({
        center: [location.longitude, location.latitude],
        zoom: 8,
        duration: 1500,
      });
    }
  }, [selectedLocationId, locations, mapLoaded]);

  const handleZoomIn = () => map.current?.zoomIn();
  const handleZoomOut = () => map.current?.zoomOut();
  const handleResetView = () => {
    map.current?.flyTo({ center: [0, 20], zoom: 1.5 });
  };

  return (
    <Card className="h-full" data-testid="water-risk-map">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2 text-base">
              <Droplets className="h-4 w-4 text-blue-300" />
              Water Risk Map
            </CardTitle>
            <CardDescription className="text-xs">
              Click markers to view location details
            </CardDescription>
          </div>
          <div className="flex items-center gap-1">
            <Button 
              variant="ghost" 
              size="icon" 
              className="h-8 w-8"
              onClick={() => setMapStyle(s => s === 'light' ? 'dark' : 'light')}
            >
              <Layers className="h-4 w-4" />
            </Button>
            <Button variant="ghost" size="icon" className="h-8 w-8" onClick={handleZoomIn}>
              <ZoomIn className="h-4 w-4" />
            </Button>
            <Button variant="ghost" size="icon" className="h-8 w-8" onClick={handleZoomOut}>
              <ZoomOut className="h-4 w-4" />
            </Button>
            <Button variant="ghost" size="icon" className="h-8 w-8" onClick={handleResetView}>
              <Locate className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-0 relative">
        <div 
          ref={mapContainer} 
          className="w-full h-[400px] rounded-b-lg"
          style={{ minHeight: '400px' }}
        />
        
        {/* Legend */}
        <div className="absolute bottom-4 left-4 bg-white/90 dark:bg-[#0d1424]/60 p-3 rounded-lg shadow-lg text-xs">
          <div className="font-medium mb-2">Water Stress Level</div>
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full" style={{ backgroundColor: '#ef4444' }} />
              <span>Extremely High (4-5)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full" style={{ backgroundColor: '#f97316' }} />
              <span>High (3-4)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full" style={{ backgroundColor: '#eab308' }} />
              <span>Medium (2-3)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full" style={{ backgroundColor: '#22c55e' }} />
              <span>Low (0-2)</span>
            </div>
          </div>
        </div>

        {/* Stats Badge */}
        <div className="absolute top-4 left-4 bg-white/90 dark:bg-[#0d1424]/60 p-2 rounded-lg shadow text-xs">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-amber-500" />
            <span>
              {locations.filter(l => (l.water_stress || 0) >= 3).length} High Risk
            </span>
          </div>
        </div>
      </CardContent>

      <style>{`
        @keyframes pulse {
          0% { transform: scale(1); opacity: 0.4; }
          50% { transform: scale(1.5); opacity: 0; }
          100% { transform: scale(1); opacity: 0.4; }
        }
      `}</style>
    </Card>
  );
}

export function WaterRiskMap(props) {
  return (
    <MapboxTokenGate height="460px">
      {(token) => <WaterRiskMapInner {...props} accessToken={token} />}
    </MapboxTokenGate>
  );
}

export default WaterRiskMap;
