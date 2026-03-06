/**
 * GeographicMap Component
 * Displays carbon projects on a map using Mapbox GL
 */

import React, { useState, useCallback, useMemo, useRef, useEffect } from 'react';
import { MapPin } from 'lucide-react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import { MapboxTokenGate } from '../../../../components/shared/MapboxTokenGate';

// Country coordinates for projects without specific coordinates
const COUNTRY_COORDS = {
  US: { lat: 39.8283, lng: -98.5795 },
  CN: { lat: 35.8617, lng: 104.1954 },
  IN: { lat: 20.5937, lng: 78.9629 },
  BR: { lat: -14.2350, lng: -51.9253 },
  ID: { lat: -0.7893, lng: 113.9213 },
  DE: { lat: 51.1657, lng: 10.4515 },
  GB: { lat: 55.3781, lng: -3.4360 },
  JP: { lat: 36.2048, lng: 138.2529 },
  AU: { lat: -25.2744, lng: 133.7751 },
  KE: { lat: -0.0236, lng: 37.9062 },
  NG: { lat: 9.0820, lng: 8.6753 },
  DEFAULT: { lat: 0, lng: 0 }
};

const getRiskColor = (riskLevel) => {
  switch (riskLevel?.toLowerCase()) {
    case 'low': return '#10B981';
    case 'medium': return '#F59E0B';
    case 'high': return '#EF4444';
    default: return '#3B82F6';
  }
};

const GeographicMapInner = ({
  projects = [],
  geoDistribution = [],
  height = 400,
  onProjectClick,
  accessToken,
}) => {
  if (accessToken) mapboxgl.accessToken = accessToken;
  const mapContainer = useRef(null);
  const map = useRef(null);
  const markersRef = useRef([]);
  const [mapLoaded, setMapLoaded] = useState(false);

  // Convert projects to markers
  const markers = useMemo(() => {
    const result = [];
    
    projects.forEach((project) => {
      let coords = null;
      
      // Use project coordinates if available
      if (project.coordinates?.lat && project.coordinates?.lng) {
        coords = project.coordinates;
      } else if (project.country_code && COUNTRY_COORDS[project.country_code]) {
        // Use country center with some jitter for multiple projects
        const base = COUNTRY_COORDS[project.country_code];
        coords = {
          lat: base.lat + (Math.random() - 0.5) * 5,
          lng: base.lng + (Math.random() - 0.5) * 5
        };
      }
      
      if (coords) {
        result.push({
          ...project,
          latitude: coords.lat,
          longitude: coords.lng
        });
      }
    });
    
    return result;
  }, [projects]);

  // Initialize map
  useEffect(() => {
    if (map.current) return; // Already initialized
    
    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: 'mapbox://styles/mapbox/light-v11',
      center: [0, 20],
      zoom: 1.5
    });

    map.current.addControl(new mapboxgl.NavigationControl(), 'top-right');
    
    map.current.on('load', () => {
      setMapLoaded(true);
    });

    return () => {
      map.current?.remove();
      map.current = null;
    };
  }, []);

  // Add markers when map is loaded
  useEffect(() => {
    if (!mapLoaded || !map.current) return;

    // Clear existing markers
    markersRef.current.forEach(marker => marker.remove());
    markersRef.current = [];

    // Add new markers
    markers.forEach((project) => {
      const el = document.createElement('div');
      el.className = 'project-marker';
      el.style.cssText = `
        width: 24px;
        height: 24px;
        cursor: pointer;
        transition: transform 0.2s;
      `;
      el.innerHTML = `
        <svg viewBox="0 0 24 24" fill="${getRiskColor(project.risk_level)}" stroke="white" stroke-width="1">
          <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>
          <circle cx="12" cy="10" r="3" fill="white"/>
        </svg>
      `;
      
      el.addEventListener('mouseenter', () => {
        el.style.transform = 'scale(1.2)';
      });
      el.addEventListener('mouseleave', () => {
        el.style.transform = 'scale(1)';
      });

      const popup = new mapboxgl.Popup({ offset: 25 }).setHTML(`
        <div style="padding: 8px; min-width: 160px;">
          <h4 style="font-weight: 600; color: #1e293b; font-size: 13px; margin-bottom: 4px;">${project.name}</h4>
          <div style="font-size: 11px; color: #64748b;">
            <p><strong>Type:</strong> ${project.project_type?.replace(/_/g, ' ')}</p>
            <p><strong>Credits:</strong> ${project.annual_credits?.toLocaleString()} tCO2e/yr</p>
            <p><strong>Standard:</strong> ${project.standard}</p>
            <p><strong>Risk:</strong> <span style="color: ${getRiskColor(project.risk_level)}">${project.risk_level || 'N/A'}</span></p>
          </div>
        </div>
      `);

      const marker = new mapboxgl.Marker(el)
        .setLngLat([project.longitude, project.latitude])
        .setPopup(popup)
        .addTo(map.current);

      el.addEventListener('click', () => {
        if (onProjectClick) onProjectClick(project);
      });

      markersRef.current.push(marker);
    });
  }, [mapLoaded, markers, onProjectClick]);

  return (
    <div className="bg-[#0d1424] rounded-xl border border-white/[0.06] p-6" data-testid="geographic-map">
      <h3 className="text-lg font-semibold text-white mb-4">
        Project Locations
      </h3>
      
      <div 
        ref={mapContainer} 
        className="rounded-lg overflow-hidden border border-white/[0.06]" 
        style={{ height }}
      />
      
      {/* Legend */}
      <div className="mt-4 flex items-center gap-4 text-xs text-white/40">
        <span className="font-medium">Risk Level:</span>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded-full bg-emerald-500" />
          <span>Low</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded-full bg-amber-500" />
          <span>Medium</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded-full bg-rose-500" />
          <span>High</span>
        </div>
      </div>
      
      {/* Distribution summary */}
      {geoDistribution.length > 0 && (
        <div className="mt-4 pt-4 border-t border-white/[0.04]">
          <p className="text-xs font-medium text-white/40 mb-2">Distribution by Country</p>
          <div className="flex flex-wrap gap-2">
            {geoDistribution.map((geo) => (
              <div 
                key={geo.country_code}
                className="px-2 py-1 bg-white/[0.06] rounded text-xs"
              >
                <span className="font-medium">{geo.country_code}:</span>{' '}
                {geo.project_count} project{geo.project_count !== 1 ? 's' : ''} ({geo.total_credits?.toLocaleString()} tCO2e)
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export const GeographicMap = (props) => {
  const { height = 400, ...rest } = props;
  return (
    <MapboxTokenGate height={`${height}px`}>
      {(token) => <GeographicMapInner {...rest} height={height} accessToken={token} />}
    </MapboxTokenGate>
  );
};

export default GeographicMap;
