import React, { useState, useEffect } from 'react';
import { Search, Plus, ChevronDown, Briefcase, Building2 } from 'lucide-react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Popover, PopoverContent, PopoverTrigger } from '../ui/popover';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../ui/dialog';
import { Label } from '../ui/label';
import { Textarea } from '../ui/textarea';
import { ScrollArea } from '../ui/scroll-area';
import { Skeleton } from '../ui/skeleton';
import { Badge } from '../ui/badge';
import { cn } from '../../lib/utils';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export function PortfolioSelector({ 
  selectedPortfolio, 
  onSelect, 
  className 
}) {
  const [open, setOpen] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);
  const [search, setSearch] = useState('');
  const [portfolios, setPortfolios] = useState([]);
  const [loading, setLoading] = useState(false);
  const [newName, setNewName] = useState('');
  const [newDescription, setNewDescription] = useState('');
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    fetchPortfolios();
  }, []);

  const fetchPortfolios = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/portfolios`);
      const data = await res.json();
      setPortfolios(data.portfolios || []);
    } catch (error) {
      console.error('Failed to fetch portfolios:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    if (!newName.trim()) return;
    
    setCreating(true);
    try {
      const res = await fetch(`${API_URL}/api/portfolios`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: newName, description: newDescription }),
      });
      const data = await res.json();
      await fetchPortfolios();
      onSelect(data);
      setCreateOpen(false);
      setNewName('');
      setNewDescription('');
    } catch (error) {
      console.error('Failed to create portfolio:', error);
    } finally {
      setCreating(false);
    }
  };

  const filteredPortfolios = portfolios.filter(p => 
    p.name.toLowerCase().includes(search.toLowerCase())
  );

  const formatCurrency = (value) => {
    if (value >= 1e9) return `$${(value / 1e9).toFixed(1)}B`;
    if (value >= 1e6) return `$${(value / 1e6).toFixed(1)}M`;
    if (value >= 1e3) return `$${(value / 1e3).toFixed(1)}K`;
    return `$${value.toFixed(0)}`;
  };

  return (
    <>
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <Button
            variant="outline"
            role="combobox"
            aria-expanded={open}
            className={cn("justify-between min-w-[280px]", className)}
            data-testid="portfolio-selector-trigger"
          >
            {selectedPortfolio ? (
              <div className="flex items-center gap-2">
                <Briefcase className="h-4 w-4 text-muted-foreground" />
                <span className="truncate max-w-[180px]">{selectedPortfolio.name}</span>
                <Badge variant="secondary" className="text-xs">
                  {selectedPortfolio.num_assets || 0} assets
                </Badge>
              </div>
            ) : (
              <span className="text-muted-foreground">Select portfolio...</span>
            )}
            <ChevronDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-[320px] p-0" align="start">
          <div className="p-3 border-b">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search portfolios..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9"
                data-testid="portfolio-search-input"
              />
            </div>
          </div>
          <ScrollArea className="max-h-[300px]">
            {loading ? (
              <div className="p-3 space-y-2">
                {[1, 2, 3].map(i => (
                  <Skeleton key={i} className="h-16 w-full" />
                ))}
              </div>
            ) : filteredPortfolios.length === 0 ? (
              <div className="p-6 text-center text-muted-foreground">
                <Building2 className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">No portfolios found</p>
              </div>
            ) : (
              <div className="p-2">
                {filteredPortfolios.map(portfolio => (
                  <button
                    key={portfolio.id}
                    onClick={() => {
                      onSelect(portfolio);
                      setOpen(false);
                    }}
                    className={cn(
                      "w-full p-3 rounded-lg text-left transition-colors",
                      "hover:bg-muted",
                      selectedPortfolio?.id === portfolio.id && "bg-primary/10"
                    )}
                    data-testid={`portfolio-option-${portfolio.id}`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-sm truncate">{portfolio.name}</p>
                        <p className="text-xs text-muted-foreground truncate">
                          {portfolio.description || 'No description'}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3 mt-2 text-xs text-muted-foreground">
                      <span>{portfolio.num_assets || 0} assets</span>
                      <span>•</span>
                      <span>{formatCurrency(portfolio.total_exposure || 0)}</span>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </ScrollArea>
          <div className="p-2 border-t">
            <Button
              variant="ghost"
              className="w-full justify-start"
              onClick={() => {
                setOpen(false);
                setCreateOpen(true);
              }}
              data-testid="create-portfolio-button"
            >
              <Plus className="h-4 w-4 mr-2" />
              Create new portfolio
            </Button>
          </div>
        </PopoverContent>
      </Popover>

      {/* Create Portfolio Dialog */}
      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent data-testid="create-portfolio-dialog">
          <DialogHeader>
            <DialogTitle>Create New Portfolio</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="portfolio-name">Portfolio Name</Label>
              <Input
                id="portfolio-name"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                placeholder="e.g., Climate Risk Portfolio Q1"
                data-testid="new-portfolio-name"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="portfolio-description">Description</Label>
              <Textarea
                id="portfolio-description"
                value={newDescription}
                onChange={(e) => setNewDescription(e.target.value)}
                placeholder="Brief description of the portfolio..."
                data-testid="new-portfolio-description"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateOpen(false)}>
              Cancel
            </Button>
            <Button 
              onClick={handleCreate} 
              disabled={!newName.trim() || creating}
              data-testid="confirm-create-portfolio"
            >
              {creating ? 'Creating...' : 'Create Portfolio'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
