/**
 * GeographicMap Component
 * Displays carbon projects on a map using Mapbox GL
 */

import React, { useState, useCallback, useMemo } from 'react';
// Import from explicit path to avoid webpack resolution issues
import Map from 'react-map-gl/dist/esm/components/map';
import Marker from 'react-map-gl/dist/esm/components/marker';
import Popup from 'react-map-gl/dist/esm/components/popup';
import NavigationControl from 'react-map-gl/dist/esm/components/navigation-control';
import { MapPin } from 'lucide-react';
import 'mapbox-gl/dist/mapbox-gl.css';

const MAPBOX_TOKEN = process.env.REACT_APP_MAPBOX_TOKEN || 'pk.eyJ1IjoiY2hvcHJhc2FoaWwzIiwiYSI6ImNtanEzbnRqOTN0anEzZG9idjg5Mm9kdTkifQ.zxCEdfkhCT5Q1AbkeRyEEw';

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

export const GeographicMap = ({ 
  projects = [],
  geoDistribution = [],
  height = 400,
  onProjectClick
}) => {
  const [popupInfo, setPopupInfo] = useState(null);
  const [viewState, setViewState] = useState({
    latitude: 20,
    longitude: 0,
    zoom: 1.5
  });

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

  const handleMarkerClick = useCallback((project) => {
    setPopupInfo(project);
    if (onProjectClick) {
      onProjectClick(project);
    }
  }, [onProjectClick]);

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6" data-testid="geographic-map">
      <h3 className="text-lg font-semibold text-slate-900 mb-4">
        Project Locations
      </h3>
      
      <div className="rounded-lg overflow-hidden border border-slate-200" style={{ height }}>
        <Map
          {...viewState}
          onMove={(evt) => setViewState(evt.viewState)}
          mapStyle="mapbox://styles/mapbox/light-v11"
          mapboxAccessToken={MAPBOX_TOKEN}
          style={{ width: '100%', height: '100%' }}
        >
          <NavigationControl position="top-right" />
          
          {markers.map((project, index) => (
            <Marker
              key={project.id || index}
              latitude={project.latitude}
              longitude={project.longitude}
              anchor="bottom"
              onClick={(e) => {
                e.originalEvent.stopPropagation();
                handleMarkerClick(project);
              }}
            >
              <div 
                className="cursor-pointer transition-transform hover:scale-110"
                style={{ color: getRiskColor(project.risk_level) }}
              >
                <MapPin className="w-6 h-6 drop-shadow-md" fill="currentColor" />
              </div>
            </Marker>
          ))}
          
          {popupInfo && (
            <Popup
              anchor="top"
              latitude={popupInfo.latitude}
              longitude={popupInfo.longitude}
              onClose={() => setPopupInfo(null)}
              closeOnClick={false}
            >
              <div className="p-2 min-w-[180px]">
                <h4 className="font-semibold text-slate-900 text-sm mb-1">
                  {popupInfo.name}
                </h4>
                <div className="text-xs text-slate-600 space-y-1">
                  <p><span className="font-medium">Type:</span> {popupInfo.project_type?.replace(/_/g, ' ')}</p>
                  <p><span className="font-medium">Credits:</span> {popupInfo.annual_credits?.toLocaleString()} tCO2e/yr</p>
                  <p><span className="font-medium">Standard:</span> {popupInfo.standard}</p>
                  <p>
                    <span className="font-medium">Risk:</span>{' '}
                    <span style={{ color: getRiskColor(popupInfo.risk_level) }}>
                      {popupInfo.risk_level || 'N/A'}
                    </span>
                  </p>
                </div>
              </div>
            </Popup>
          )}
        </Map>
      </div>
      
      {/* Legend */}
      <div className="mt-4 flex items-center gap-4 text-xs text-slate-500">
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
        <div className="mt-4 pt-4 border-t border-slate-100">
          <p className="text-xs font-medium text-slate-500 mb-2">Distribution by Country</p>
          <div className="flex flex-wrap gap-2">
            {geoDistribution.map((geo) => (
              <div 
                key={geo.country_code}
                className="px-2 py-1 bg-slate-100 rounded text-xs"
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

export default GeographicMap;
