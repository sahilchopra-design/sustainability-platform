import React, { useMemo, useState } from 'react';
import { Plus, Search, Filter, Download, ArrowUpDown, Edit2, Trash2, MoreVertical } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../ui/table';
import { Checkbox } from '../ui/checkbox';
import { Badge } from '../ui/badge';
import { ScrollArea } from '../ui/scroll-area';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '../ui/dropdown-menu';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../ui/select';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '../ui/popover';
import { BulkEditToolbar } from './BulkEditToolbar';
import { Holding } from '../../types/portfolio';
import { cn } from '../../lib/utils';

export interface HoldingsManagerProps {
  holdings: Holding[];
  selectedIds: string[];
  onSelectIds: (ids: string[]) => void;
  onAdd: () => void;
  onEdit: (holding: Holding) => void;
  onDelete: (holdingId: string) => void;
  onBulkDelete: (holdingIds: string[]) => void;
  onExport: (holdingIds: string[]) => void;
  loading?: boolean;
}

type SortField = 'counterparty_name' | 'exposure' | 'currency' | 'sector' | 'rating';
type SortDirection = 'asc' | 'desc';

export const HoldingsManager: React.FC<HoldingsManagerProps> = ({
  holdings,
  selectedIds,
  onSelectIds,
  onAdd,
  onEdit,
  onDelete,
  onBulkDelete,
  onExport,
  loading = false,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [sectorFilter, setSectorFilter] = useState<string>('all');
  const [currencyFilter, setCurrencyFilter] = useState<string>('all');
  const [sortField, setSortField] = useState<SortField>('counterparty_name');
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc');

  // Get unique sectors and currencies
  const { sectors, currencies } = useMemo(() => {
    const sectorsSet = new Set<string>();
    const currenciesSet = new Set<string>();
    holdings.forEach((h) => {
      if (h.sector) sectorsSet.add(h.sector);
      currenciesSet.add(h.currency);
    });
    return {
      sectors: Array.from(sectorsSet).sort(),
      currencies: Array.from(currenciesSet).sort(),
    };
  }, [holdings]);

  // Filter and sort holdings
  const filteredHoldings = useMemo(() => {
    let result = [...holdings];

    // Search
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      result = result.filter(
        (h) =>
          h.counterparty_name.toLowerCase().includes(query) ||
          h.lei?.toLowerCase().includes(query) ||
          h.isin?.toLowerCase().includes(query)
      );
    }

    // Filters
    if (sectorFilter !== 'all') {
      result = result.filter((h) => h.sector === sectorFilter);
    }
    if (currencyFilter !== 'all') {
      result = result.filter((h) => h.currency === currencyFilter);
    }

    // Sort
    result.sort((a, b) => {
      let aVal: any = a[sortField];
      let bVal: any = b[sortField];

      if (sortField === 'exposure') {
        aVal = Number(aVal);
        bVal = Number(bVal);
      } else {
        aVal = String(aVal || '').toLowerCase();
        bVal = String(bVal || '').toLowerCase();
      }

      if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });

    return result;
  }, [holdings, searchQuery, sectorFilter, currencyFilter, sortField, sortDirection]);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection((prev) => (prev === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  const handleSelectAll = () => {
    if (selectedIds.length === filteredHoldings.length) {
      onSelectIds([]);
    } else {
      onSelectIds(filteredHoldings.map((h) => h.id));
    }
  };

  const handleSelectOne = (id: string) => {
    if (selectedIds.includes(id)) {
      onSelectIds(selectedIds.filter((hId) => hId !== id));
    } else {
      onSelectIds([...selectedIds, id]);
    }
  };

  const formatCurrency = (amount: number, currency: string): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency,
      notation: 'compact',
      maximumFractionDigits: 1,
    }).format(amount);
  };

  const allSelected = filteredHoldings.length > 0 && selectedIds.length === filteredHoldings.length;
  const someSelected = selectedIds.length > 0 && selectedIds.length < filteredHoldings.length;

  return (
    <Card data-testid="holdings-manager">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Holdings</CardTitle>
            <CardDescription className="mt-1">
              {filteredHoldings.length} of {holdings.length} holdings
            </CardDescription>
          </div>
          <Button onClick={onAdd} data-testid="add-holding-button">
            <Plus className="h-4 w-4 mr-2" />
            Add Holding
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Search and Filters */}
          <div className="flex items-center gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search by name, LEI, or ISIN..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
                data-testid="holdings-search-input"
              />
            </div>

            <Popover>
              <PopoverTrigger asChild>
                <Button variant="outline" size="sm" data-testid="holdings-filter-button">
                  <Filter className="h-4 w-4 mr-2" />
                  Filter
                  {(sectorFilter !== 'all' || currencyFilter !== 'all') && (
                    <Badge variant="secondary" className="ml-2">
                      {(sectorFilter !== 'all' ? 1 : 0) + (currencyFilter !== 'all' ? 1 : 0)}
                    </Badge>
                  )}
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-80" data-testid="holdings-filter-popover">
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label>Sector</Label>
                    <Select value={sectorFilter} onValueChange={setSectorFilter}>
                      <SelectTrigger data-testid="sector-filter-select">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">All Sectors</SelectItem>
                        {sectors.map((sector) => (
                          <SelectItem key={sector} value={sector}>
                            {sector}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Currency</Label>
                    <Select value={currencyFilter} onValueChange={setCurrencyFilter}>
                      <SelectTrigger data-testid="currency-filter-select">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">All Currencies</SelectItem>
                        {currencies.map((curr) => (
                          <SelectItem key={curr} value={curr}>
                            {curr}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </PopoverContent>
            </Popover>

            <Button
              variant="outline"
              size="sm"
              onClick={() => onExport(selectedIds.length > 0 ? selectedIds : holdings.map(h => h.id))}
              data-testid="export-holdings-button"
            >
              <Download className="h-4 w-4 mr-2" />
              Export
            </Button>
          </div>

          {/* Bulk Actions Toolbar */}
          <BulkEditToolbar
            selectedCount={selectedIds.length}
            onBulkDelete={() => onBulkDelete(selectedIds)}
            onExport={() => onExport(selectedIds)}
            onClearSelection={() => onSelectIds([])}
            disabled={loading}
          />

          {/* Holdings Table */}
          <div className="border rounded-lg overflow-hidden">
            <ScrollArea className="h-[600px]">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-12">
                      <Checkbox
                        checked={allSelected}
                        indeterminate={someSelected}
                        onCheckedChange={handleSelectAll}
                        data-testid="select-all-holdings-checkbox"
                      />
                    </TableHead>
                    <TableHead
                      className="cursor-pointer hover:bg-muted/50"
                      onClick={() => handleSort('counterparty_name')}
                      data-testid="sort-by-name"
                    >
                      <div className="flex items-center gap-2">
                        Counterparty
                        <ArrowUpDown className="h-3 w-3" />
                      </div>
                    </TableHead>
                    <TableHead
                      className="cursor-pointer hover:bg-muted/50 text-right"
                      onClick={() => handleSort('exposure')}
                      data-testid="sort-by-exposure"
                    >
                      <div className="flex items-center justify-end gap-2">
                        Exposure
                        <ArrowUpDown className="h-3 w-3" />
                      </div>
                    </TableHead>
                    <TableHead
                      className="cursor-pointer hover:bg-muted/50"
                      onClick={() => handleSort('currency')}
                    >
                      <div className="flex items-center gap-2">
                        Currency
                        <ArrowUpDown className="h-3 w-3" />
                      </div>
                    </TableHead>
                    <TableHead
                      className="cursor-pointer hover:bg-muted/50"
                      onClick={() => handleSort('sector')}
                    >
                      <div className="flex items-center gap-2">
                        Sector
                        <ArrowUpDown className="h-3 w-3" />
                      </div>
                    </TableHead>
                    <TableHead
                      className="cursor-pointer hover:bg-muted/50"
                      onClick={() => handleSort('rating')}
                    >
                      <div className="flex items-center gap-2">
                        Rating
                        <ArrowUpDown className="h-3 w-3" />
                      </div>
                    </TableHead>
                    <TableHead className="w-16">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {loading ? (
                    <TableRow>
                      <TableCell colSpan={7} className="text-center py-12">
                        <div className="flex items-center justify-center gap-2 text-muted-foreground">
                          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
                          <span>Loading holdings...</span>
                        </div>
                      </TableCell>
                    </TableRow>
                  ) : filteredHoldings.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={7} className="text-center py-12 text-muted-foreground">
                        No holdings found
                      </TableCell>
                    </TableRow>
                  ) : (
                    filteredHoldings.map((holding) => (
                      <TableRow
                        key={holding.id}
                        className={cn(selectedIds.includes(holding.id) && 'bg-accent/50')}
                        data-testid={`holding-row-${holding.id}`}
                      >
                        <TableCell>
                          <Checkbox
                            checked={selectedIds.includes(holding.id)}
                            onCheckedChange={() => handleSelectOne(holding.id)}
                            data-testid={`select-holding-${holding.id}`}
                          />
                        </TableCell>
                        <TableCell>
                          <div>
                            <p className="font-medium text-sm">{holding.counterparty_name}</p>
                            {holding.lei && (
                              <p className="text-xs text-muted-foreground font-mono">
                                {holding.lei}
                              </p>
                            )}
                          </div>
                        </TableCell>
                        <TableCell className="text-right font-medium tabular-nums">
                          {formatCurrency(holding.exposure, holding.currency)}
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline" className="font-mono">
                            {holding.currency}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <span className="text-sm">{holding.sector || '-'}</span>
                        </TableCell>
                        <TableCell>
                          {holding.rating ? (
                            <Badge variant="secondary">{holding.rating}</Badge>
                          ) : (
                            <span className="text-sm text-muted-foreground">-</span>
                          )}
                        </TableCell>
                        <TableCell>
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button
                                variant="ghost"
                                size="sm"
                                className="h-8 w-8 p-0"
                                data-testid={`holding-actions-${holding.id}`}
                              >
                                <MoreVertical className="h-4 w-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuItem
                                onClick={() => onEdit(holding)}
                                data-testid={`edit-holding-${holding.id}`}
                              >
                                <Edit2 className="h-4 w-4 mr-2" />
                                Edit
                              </DropdownMenuItem>
                              <DropdownMenuSeparator />
                              <DropdownMenuItem
                                onClick={() => onDelete(holding.id)}
                                className="text-destructive focus:text-destructive"
                                data-testid={`delete-holding-${holding.id}`}
                              >
                                <Trash2 className="h-4 w-4 mr-2" />
                                Delete
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </ScrollArea>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

// Missing Label component - add this import at the top
import { Label } from '../ui/label';