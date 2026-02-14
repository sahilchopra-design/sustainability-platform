import React, { useState, useMemo } from 'react';
import { 
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
} from '@tanstack/react-table';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../ui/table';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Badge } from '../ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Skeleton } from '../ui/skeleton';
import { 
  Search, Download, ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight,
  ArrowUpDown, ArrowUp, ArrowDown, Users, Building2 
} from 'lucide-react';
import { cn } from '../../lib/utils';

const RATING_COLORS = {
  AAA: 'bg-success/20 text-success',
  AA: 'bg-success/20 text-success',
  A: 'bg-info/20 text-info',
  BBB: 'bg-info/20 text-info',
  BB: 'bg-warning/20 text-warning',
  B: 'bg-warning/20 text-warning',
  CCC: 'bg-destructive/20 text-destructive',
  CC: 'bg-destructive/20 text-destructive',
  C: 'bg-destructive/20 text-destructive',
  D: 'bg-destructive/20 text-destructive',
  NR: 'bg-muted text-muted-foreground',
};

function formatCurrency(value) {
  if (!value && value !== 0) return '--';
  if (Math.abs(value) >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
  if (Math.abs(value) >= 1e6) return `$${(value / 1e6).toFixed(2)}M`;
  if (Math.abs(value) >= 1e3) return `$${(value / 1e3).toFixed(0)}K`;
  return `$${value.toFixed(0)}`;
}

function formatPercent(value) {
  if (!value && value !== 0) return '--';
  return `${(value * 100).toFixed(2)}%`;
}

export function CounterpartyTable({
  holdings = [],
  loading = false,
  onExport,
  className,
}) {
  const [sorting, setSorting] = useState([]);
  const [globalFilter, setGlobalFilter] = useState('');
  const [columnFilters, setColumnFilters] = useState([]);
  const [pagination, setPagination] = useState({ pageIndex: 0, pageSize: 10 });

  const columns = useMemo(() => [
    {
      accessorKey: 'company.name',
      header: ({ column }) => (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
          className="h-auto p-0 font-medium hover:bg-transparent"
        >
          Counterparty
          <SortIndicator sorted={column.getIsSorted()} />
        </Button>
      ),
      cell: ({ row }) => (
        <div className="flex items-center gap-2">
          <Building2 className="h-4 w-4 text-muted-foreground shrink-0" />
          <div className="min-w-0">
            <p className="font-medium truncate">{row.original.company?.name || 'Unknown'}</p>
            <p className="text-xs text-muted-foreground truncate">
              {row.original.company?.sector || '--'}
            </p>
          </div>
        </div>
      ),
    },
    {
      accessorKey: 'rating',
      header: 'Rating',
      cell: ({ row }) => {
        const rating = row.getValue('rating') || 'NR';
        return (
          <Badge variant="outline" className={cn('text-xs', RATING_COLORS[rating])}>
            {rating}
          </Badge>
        );
      },
    },
    {
      accessorKey: 'exposure',
      header: ({ column }) => (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
          className="h-auto p-0 font-medium hover:bg-transparent"
        >
          Exposure
          <SortIndicator sorted={column.getIsSorted()} />
        </Button>
      ),
      cell: ({ row }) => (
        <span className="tabular-nums">{formatCurrency(row.getValue('exposure'))}</span>
      ),
    },
    {
      accessorKey: 'base_pd',
      header: ({ column }) => (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
          className="h-auto p-0 font-medium hover:bg-transparent"
        >
          Base PD
          <SortIndicator sorted={column.getIsSorted()} />
        </Button>
      ),
      cell: ({ row }) => (
        <span className="tabular-nums">{formatPercent(row.getValue('base_pd'))}</span>
      ),
    },
    {
      accessorKey: 'base_lgd',
      header: 'LGD',
      cell: ({ row }) => (
        <span className="tabular-nums">{formatPercent(row.getValue('base_lgd'))}</span>
      ),
    },
    {
      accessorKey: 'expected_loss',
      header: ({ column }) => (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
          className="h-auto p-0 font-medium hover:bg-transparent"
        >
          Expected Loss
          <SortIndicator sorted={column.getIsSorted()} />
        </Button>
      ),
      cell: ({ row }) => {
        const exposure = row.getValue('exposure') || 0;
        const pd = row.getValue('base_pd') || 0;
        const lgd = row.getValue('base_lgd') || 0;
        const el = exposure * pd * lgd;
        return <span className="tabular-nums">{formatCurrency(el)}</span>;
      },
    },
    {
      accessorKey: 'asset_type',
      header: 'Type',
      cell: ({ row }) => (
        <Badge variant="secondary" className="text-xs">
          {row.getValue('asset_type') || 'Loan'}
        </Badge>
      ),
    },
  ], []);

  const table = useReactTable({
    data: holdings,
    columns,
    state: {
      sorting,
      globalFilter,
      columnFilters,
      pagination,
    },
    onSortingChange: setSorting,
    onGlobalFilterChange: setGlobalFilter,
    onColumnFiltersChange: setColumnFilters,
    onPaginationChange: setPagination,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
  });

  const handleExport = () => {
    const rows = table.getFilteredRowModel().rows;
    const csvContent = [
      ['Counterparty', 'Sector', 'Rating', 'Exposure', 'PD', 'LGD', 'Type'],
      ...rows.map(row => [
        row.original.company?.name || '',
        row.original.company?.sector || '',
        row.original.rating || '',
        row.original.exposure || 0,
        row.original.base_pd || 0,
        row.original.base_lgd || 0,
        row.original.asset_type || '',
      ])
    ].map(row => row.join(',')).join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'counterparty_holdings.csv';
    a.click();
    URL.revokeObjectURL(url);
    
    onExport?.();
  };

  if (loading) {
    return (
      <Card className={className}>
        <CardHeader>
          <Skeleton className="h-6 w-48" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-[400px] w-full rounded-lg" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className} data-testid="counterparty-table">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between gap-4">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5" />
              Counterparty Holdings
            </CardTitle>
            <CardDescription>
              {holdings.length} counterparties in portfolio
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search counterparties..."
                value={globalFilter}
                onChange={(e) => setGlobalFilter(e.target.value)}
                className="pl-9 w-[200px]"
                data-testid="counterparty-search"
              />
            </div>
            <Button variant="outline" onClick={handleExport} data-testid="export-table-button">
              <Download className="h-4 w-4 mr-2" />
              Export
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {holdings.length === 0 ? (
          <div className="py-12 text-center">
            <Users className="h-12 w-12 mx-auto text-muted-foreground opacity-50 mb-4" />
            <p className="text-muted-foreground">No holdings to display</p>
          </div>
        ) : (
          <>
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  {table.getHeaderGroups().map((headerGroup) => (
                    <TableRow key={headerGroup.id}>
                      {headerGroup.headers.map((header) => (
                        <TableHead key={header.id} className="whitespace-nowrap">
                          {header.isPlaceholder
                            ? null
                            : flexRender(header.column.columnDef.header, header.getContext())}
                        </TableHead>
                      ))}
                    </TableRow>
                  ))}
                </TableHeader>
                <TableBody>
                  {table.getRowModel().rows?.length ? (
                    table.getRowModel().rows.map((row) => (
                      <TableRow
                        key={row.id}
                        data-testid={`counterparty-row-${row.index}`}
                      >
                        {row.getVisibleCells().map((cell) => (
                          <TableCell key={cell.id}>
                            {flexRender(cell.column.columnDef.cell, cell.getContext())}
                          </TableCell>
                        ))}
                      </TableRow>
                    ))
                  ) : (
                    <TableRow>
                      <TableCell colSpan={columns.length} className="h-24 text-center">
                        No results found.
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </div>

            {/* Pagination */}
            <div className="flex items-center justify-between px-2 pt-4">
              <div className="text-sm text-muted-foreground">
                Showing {pagination.pageIndex * pagination.pageSize + 1} to{' '}
                {Math.min((pagination.pageIndex + 1) * pagination.pageSize, table.getFilteredRowModel().rows.length)}{' '}
                of {table.getFilteredRowModel().rows.length} results
              </div>
              <div className="flex items-center gap-2">
                <Select
                  value={pagination.pageSize.toString()}
                  onValueChange={(value) => setPagination({ ...pagination, pageSize: Number(value) })}
                >
                  <SelectTrigger className="w-[70px]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {[10, 20, 30, 50].map((size) => (
                      <SelectItem key={size} value={size.toString()}>
                        {size}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <div className="flex gap-1">
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={() => table.setPageIndex(0)}
                    disabled={!table.getCanPreviousPage()}
                    data-testid="pagination-first"
                  >
                    <ChevronsLeft className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={() => table.previousPage()}
                    disabled={!table.getCanPreviousPage()}
                    data-testid="pagination-prev"
                  >
                    <ChevronLeft className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={() => table.nextPage()}
                    disabled={!table.getCanNextPage()}
                    data-testid="pagination-next"
                  >
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={() => table.setPageIndex(table.getPageCount() - 1)}
                    disabled={!table.getCanNextPage()}
                    data-testid="pagination-last"
                  >
                    <ChevronsRight className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}

function SortIndicator({ sorted }) {
  if (!sorted) return <ArrowUpDown className="ml-1 h-3 w-3" />;
  if (sorted === 'asc') return <ArrowUp className="ml-1 h-3 w-3" />;
  return <ArrowDown className="ml-1 h-3 w-3" />;
}
