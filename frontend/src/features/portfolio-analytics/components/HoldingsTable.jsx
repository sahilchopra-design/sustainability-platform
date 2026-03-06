/**
 * Holdings Table Component
 * Displays portfolio holdings with key metrics
 */
import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../../components/ui/card';
import { Badge } from '../../../components/ui/badge';
import { Button } from '../../../components/ui/button';
import { Input } from '../../../components/ui/input';
import { Skeleton } from '../../../components/ui/skeleton';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow
} from '../../../components/ui/table';
import { Building2, Search, ArrowUpDown, ChevronUp, ChevronDown } from 'lucide-react';

const PROPERTY_TYPE_COLORS = {
  office: 'bg-blue-500/10 text-blue-300',
  retail: 'bg-purple-500/10 text-purple-300',
  industrial: 'bg-amber-500/10 text-amber-400',
  multifamily: 'bg-emerald-500/10 text-emerald-400',
  hotel: 'bg-pink-50 text-pink-700',
  mixed_use: 'bg-cyan-50 text-cyan-700',
};

function formatCurrency(value) {
  if (!value) return '-';
  const num = parseFloat(value);
  if (num >= 1e9) return `$${(num / 1e9).toFixed(2)}B`;
  if (num >= 1e6) return `$${(num / 1e6).toFixed(1)}M`;
  if (num >= 1e3) return `$${(num / 1e3).toFixed(0)}K`;
  return `$${num.toLocaleString()}`;
}

function formatPercent(value) {
  if (!value && value !== 0) return '-';
  return `${(parseFloat(value) * 100).toFixed(0)}%`;
}

export function HoldingsTable({ holdings, isLoading }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [sortField, setSortField] = useState('current_value');
  const [sortDir, setSortDir] = useState('desc');
  
  if (isLoading) {
    return (
      <Card className="bg-[#0d1424]" data-testid="holdings-table-loading">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-semibold text-white/70">Portfolio Holdings</CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-8 w-64 mb-4" />
          <div className="space-y-2">
            {[...Array(5)].map((_, i) => (
              <Skeleton key={i} className="h-12 w-full" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }
  
  const items = holdings?.items || [];
  
  // Filter
  const filtered = items.filter(h => 
    h.property_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    h.property_location?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    h.property_type?.toLowerCase().includes(searchTerm.toLowerCase())
  );
  
  // Sort
  const sorted = [...filtered].sort((a, b) => {
    let aVal = a[sortField] || 0;
    let bVal = b[sortField] || 0;
    if (typeof aVal === 'string') aVal = aVal.toLowerCase();
    if (typeof bVal === 'string') bVal = bVal.toLowerCase();
    if (aVal < bVal) return sortDir === 'asc' ? -1 : 1;
    if (aVal > bVal) return sortDir === 'asc' ? 1 : -1;
    return 0;
  });
  
  const handleSort = (field) => {
    if (sortField === field) {
      setSortDir(sortDir === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDir('desc');
    }
  };
  
  const SortIcon = ({ field }) => {
    if (sortField !== field) return <ArrowUpDown className="h-3 w-3 opacity-30" />;
    return sortDir === 'asc' 
      ? <ChevronUp className="h-3 w-3" /> 
      : <ChevronDown className="h-3 w-3" />;
  };
  
  return (
    <Card className="bg-[#0d1424]" data-testid="holdings-table">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-semibold text-white/70 flex items-center gap-2">
            <Building2 className="h-4 w-4 text-blue-500" />
            Portfolio Holdings
            <Badge variant="outline" className="ml-2">
              {holdings?.total || 0} properties
            </Badge>
          </CardTitle>
          <div className="text-sm text-white/60">
            Total Value: <span className="font-semibold">{formatCurrency(holdings?.total_value)}</span>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {/* Search */}
        <div className="relative mb-4">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-white/30" />
          <Input
            placeholder="Search by name, location, or type..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-9"
            data-testid="holdings-search"
          />
        </div>
        
        {/* Table */}
        <div className="border rounded-lg overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow className="bg-white/[0.02]">
                <TableHead className="cursor-pointer" onClick={() => handleSort('property_name')}>
                  <div className="flex items-center gap-1">
                    Property <SortIcon field="property_name" />
                  </div>
                </TableHead>
                <TableHead>Type</TableHead>
                <TableHead className="cursor-pointer" onClick={() => handleSort('current_value')}>
                  <div className="flex items-center gap-1">
                    Value <SortIcon field="current_value" />
                  </div>
                </TableHead>
                <TableHead className="cursor-pointer" onClick={() => handleSort('annual_income')}>
                  <div className="flex items-center gap-1">
                    Income <SortIcon field="annual_income" />
                  </div>
                </TableHead>
                <TableHead>Ownership</TableHead>
                <TableHead className="cursor-pointer" onClick={() => handleSort('unrealized_gain_loss')}>
                  <div className="flex items-center gap-1">
                    Gain/Loss <SortIcon field="unrealized_gain_loss" />
                  </div>
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {sorted.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center py-8 text-white/40">
                    {searchTerm ? 'No holdings match your search' : 'No holdings in this portfolio'}
                  </TableCell>
                </TableRow>
              ) : (
                sorted.map((holding) => {
                  const gainLoss = parseFloat(holding.unrealized_gain_loss || 0);
                  const isGain = gainLoss > 0;
                  
                  return (
                    <TableRow key={holding.id} data-testid={`holding-row-${holding.id}`}>
                      <TableCell>
                        <div>
                          <p className="font-medium text-white/90">{holding.property_name || 'Unknown'}</p>
                          <p className="text-xs text-white/40">{holding.property_location || '-'}</p>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge 
                          variant="outline" 
                          className={PROPERTY_TYPE_COLORS[holding.property_type] || 'bg-white/[0.02] text-white/60'}
                        >
                          {holding.property_type || '-'}
                        </Badge>
                      </TableCell>
                      <TableCell className="font-medium">
                        {formatCurrency(holding.current_value)}
                      </TableCell>
                      <TableCell>
                        {formatCurrency(holding.annual_income)}
                      </TableCell>
                      <TableCell>
                        {formatPercent(holding.ownership_percentage)}
                      </TableCell>
                      <TableCell>
                        <span className={isGain ? 'text-emerald-400' : gainLoss < 0 ? 'text-red-400' : 'text-white/40'}>
                          {gainLoss > 0 ? '+' : ''}{formatCurrency(holding.unrealized_gain_loss)}
                        </span>
                      </TableCell>
                    </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
}
