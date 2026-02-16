import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../../../components/ui/card';
import { Button } from '../../../../components/ui/button';
import { Badge } from '../../../../components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../../../components/ui/select';
import { Slider } from '../../../../components/ui/slider';
import { Alert, AlertDescription, AlertTitle } from '../../../../components/ui/alert';
import { 
  TreePine, MapPin, AlertTriangle, Shield, Globe, 
  ChevronRight, Filter, Search 
} from 'lucide-react';
import { natureRiskApi } from '../../api/natureRiskApi';

const SITE_TYPE_COLORS = {
  'world_heritage': 'bg-purple-500',
  'ramsar': 'bg-blue-500',
  'key_biodiversity_area': 'bg-green-500',
  'protected_area': 'bg-yellow-500',
  'iba': 'bg-cyan-500'
};

const SITE_TYPE_LABELS = {
  'world_heritage': 'World Heritage',
  'ramsar': 'Ramsar Wetland',
  'key_biodiversity_area': 'KBA',
  'protected_area': 'Protected Area',
  'iba': 'Important Bird Area'
};

export function BiodiversityOverlaps() {
  const [sites, setSites] = useState([]);
  const [countryFilter, setCountryFilter] = useState('');
  const [siteTypeFilter, setSiteTypeFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedSite, setSelectedSite] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadSites();
  }, []);

  const loadSites = async () => {
    try {
      setLoading(true);
      const data = await natureRiskApi.getBiodiversitySites();
      setSites(data);
    } catch (err) {
      console.error('Error loading sites:', err);
    } finally {
      setLoading(false);
    }
  };

  const filteredSites = sites.filter(site => {
    if (countryFilter && site.country_code !== countryFilter) return false;
    if (siteTypeFilter && site.site_type !== siteTypeFilter) return false;
    if (searchQuery && !site.site_name.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    return true;
  });

  const countries = [...new Set(sites.map(s => s.country_code))].sort();
  const siteTypes = [...new Set(sites.map(s => s.site_type))];

  // Summary stats
  const totalArea = filteredSites.reduce((sum, s) => sum + (s.area_km2 || 0), 0);
  const siteTypeCounts = filteredSites.reduce((acc, s) => {
    acc[s.site_type] = (acc[s.site_type] || 0) + 1;
    return acc;
  }, {});

  return (
    <div className="space-y-6" data-testid="biodiversity-overlaps">
      {/* Header */}
      <Card className="bg-white dark:bg-slate-800">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TreePine className="h-5 w-5 text-green-600" />
            Biodiversity Sites Browser
          </CardTitle>
          <CardDescription>
            Explore protected areas, KBAs, and Ramsar sites from global databases
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
              <input
                type="text"
                placeholder="Search sites..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
              />
            </div>
            <Select value={countryFilter} onValueChange={setCountryFilter}>
              <SelectTrigger>
                <SelectValue placeholder="All Countries" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">All Countries</SelectItem>
                {countries.map(code => (
                  <SelectItem key={code} value={code}>{code}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={siteTypeFilter} onValueChange={setSiteTypeFilter}>
              <SelectTrigger>
                <SelectValue placeholder="All Site Types" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">All Site Types</SelectItem>
                {siteTypes.map(type => (
                  <SelectItem key={type} value={type}>
                    {SITE_TYPE_LABELS[type] || type}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Badge variant="outline" className="h-10 flex items-center justify-center gap-2">
              <Globe className="h-4 w-4" />
              {filteredSites.length} sites • {(totalArea / 1000).toFixed(0)}k km²
            </Badge>
          </div>
        </CardContent>
      </Card>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {Object.entries(SITE_TYPE_LABELS).map(([type, label]) => (
          <Card 
            key={type} 
            className={`bg-white dark:bg-slate-800 cursor-pointer transition-all hover:shadow-lg ${
              siteTypeFilter === type ? 'ring-2 ring-green-500' : ''
            }`}
            onClick={() => setSiteTypeFilter(siteTypeFilter === type ? '' : type)}
          >
            <CardContent className="pt-4 pb-4">
              <div className="flex items-center gap-2 mb-2">
                <div className={`w-3 h-3 rounded-full ${SITE_TYPE_COLORS[type]}`} />
                <span className="text-xs text-slate-500">{label}</span>
              </div>
              <p className="text-xl font-bold">{siteTypeCounts[type] || 0}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Sites List */}
        <Card className="bg-white dark:bg-slate-800 lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-lg">Protected Sites</CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="text-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600 mx-auto"></div>
              </div>
            ) : (
              <div className="space-y-2 max-h-[500px] overflow-y-auto">
                {filteredSites.map(site => (
                  <div
                    key={site.id}
                    className={`p-4 rounded-lg cursor-pointer transition-all ${
                      selectedSite?.id === site.id
                        ? 'bg-green-50 dark:bg-green-900/30 border-2 border-green-500'
                        : 'bg-slate-50 dark:bg-slate-700/50 hover:bg-slate-100 dark:hover:bg-slate-700'
                    }`}
                    onClick={() => setSelectedSite(site)}
                    data-testid={`site-${site.id}`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className={`w-3 h-3 rounded-full ${SITE_TYPE_COLORS[site.site_type] || 'bg-gray-500'}`} />
                        <div>
                          <p className="font-medium text-sm">{site.site_name}</p>
                          <p className="text-xs text-slate-500">
                            {site.country_code} • {site.ecosystem_type || 'Unknown ecosystem'}
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <Badge variant="outline" className="text-xs">
                          {SITE_TYPE_LABELS[site.site_type] || site.site_type}
                        </Badge>
                        {site.area_km2 && (
                          <p className="text-xs text-slate-500 mt-1">
                            {site.area_km2.toLocaleString()} km²
                          </p>
                        )}
                      </div>
                    </div>
                    {site.key_species?.length > 0 && (
                      <div className="flex gap-1 mt-2 flex-wrap">
                        {site.key_species.slice(0, 3).map((species, i) => (
                          <Badge key={i} variant="secondary" className="text-xs">
                            {species.replace('_', ' ')}
                          </Badge>
                        ))}
                        {site.key_species.length > 3 && (
                          <Badge variant="secondary" className="text-xs">
                            +{site.key_species.length - 3} more
                          </Badge>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Site Details */}
        <Card className="bg-white dark:bg-slate-800">
          <CardHeader>
            <CardTitle className="text-lg">Site Details</CardTitle>
          </CardHeader>
          <CardContent>
            {selectedSite ? (
              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <div className={`w-4 h-4 rounded-full ${SITE_TYPE_COLORS[selectedSite.site_type] || 'bg-gray-500'}`} />
                  <div>
                    <h3 className="font-semibold">{selectedSite.site_name}</h3>
                    <p className="text-sm text-slate-500">
                      {SITE_TYPE_LABELS[selectedSite.site_type] || selectedSite.site_type}
                    </p>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="p-3 bg-slate-50 dark:bg-slate-700/50 rounded-lg">
                    <p className="text-xs text-slate-500">Country</p>
                    <p className="font-medium">{selectedSite.country_code}</p>
                  </div>
                  <div className="p-3 bg-slate-50 dark:bg-slate-700/50 rounded-lg">
                    <p className="text-xs text-slate-500">Area</p>
                    <p className="font-medium">{selectedSite.area_km2?.toLocaleString() || 'N/A'} km²</p>
                  </div>
                  <div className="p-3 bg-slate-50 dark:bg-slate-700/50 rounded-lg">
                    <p className="text-xs text-slate-500">Ecosystem</p>
                    <p className="font-medium">{selectedSite.ecosystem_type || 'Unknown'}</p>
                  </div>
                  <div className="p-3 bg-slate-50 dark:bg-slate-700/50 rounded-lg">
                    <p className="text-xs text-slate-500">Designated</p>
                    <p className="font-medium">{selectedSite.designation_year || 'N/A'}</p>
                  </div>
                </div>

                {selectedSite.iucn_category && (
                  <div className="p-3 bg-slate-50 dark:bg-slate-700/50 rounded-lg">
                    <p className="text-xs text-slate-500">IUCN Category</p>
                    <Badge className="mt-1">{selectedSite.iucn_category}</Badge>
                  </div>
                )}

                {selectedSite.latitude && selectedSite.longitude && (
                  <div className="p-3 bg-slate-50 dark:bg-slate-700/50 rounded-lg">
                    <p className="text-xs text-slate-500">Coordinates</p>
                    <p className="font-mono text-sm">
                      {selectedSite.latitude?.toFixed(4)}, {selectedSite.longitude?.toFixed(4)}
                    </p>
                  </div>
                )}

                {selectedSite.key_species?.length > 0 && (
                  <div>
                    <p className="text-xs text-slate-500 mb-2">Key Species</p>
                    <div className="flex flex-wrap gap-1">
                      {selectedSite.key_species.map((species, i) => (
                        <Badge key={i} variant="outline" className="text-xs">
                          {species.replace('_', ' ')}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}

                <div className="pt-4 border-t">
                  <p className="text-xs text-slate-500">Data Source</p>
                  <p className="text-sm">{selectedSite.data_source || 'WDPA'}</p>
                </div>
              </div>
            ) : (
              <div className="text-center py-8 text-slate-500">
                <TreePine className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>Select a site to view details</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Info Alert */}
      <Alert className="bg-green-50 dark:bg-green-900/20 border-green-200">
        <Shield className="h-4 w-4 text-green-600" />
        <AlertTitle className="text-green-800 dark:text-green-200">Data Sources</AlertTitle>
        <AlertDescription className="text-green-700 dark:text-green-300">
          This module includes data from WDPA (World Database on Protected Areas), 
          Key Biodiversity Areas, Ramsar Convention wetlands, and BirdLife International IBAs.
        </AlertDescription>
      </Alert>
    </div>
  );
}
