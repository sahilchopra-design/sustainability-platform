// Type definitions for portfolio editing

export interface Portfolio {
  id: string;
  name: string;
  description?: string;
  currency: string;
  created_at: string;
  updated_at: string;
  total_exposure: number;
  holdings_count: number;
  metadata?: Record<string, any>;
}

export interface Holding {
  id: string;
  portfolio_id: string;
  counterparty_id: string;
  counterparty_name: string;
  exposure: number;
  currency: string;
  sector?: string;
  rating?: string;
  lei?: string;
  isin?: string;
  country?: string;
  maturity_date?: string;
  lgd?: number;
  pd?: number;
  created_at: string;
  updated_at: string;
}

export interface Counterparty {
  id: string;
  name: string;
  lei?: string;
  sector?: string;
  country?: string;
  rating?: string;
}

export interface ChangeLog {
  id: string;
  portfolio_id: string;
  action: 'create' | 'update' | 'delete' | 'bulk_update' | 'bulk_delete';
  entity_type: 'portfolio' | 'holding';
  entity_id: string;
  user_id?: string;
  timestamp: string;
  changes: {
    field: string;
    old_value: any;
    new_value: any;
  }[];
  can_undo: boolean;
}

export interface PortfolioMetrics {
  total_exposure: number;
  holdings_count: number;
  currency_distribution: Record<string, number>;
  sector_distribution: Record<string, number>;
  rating_distribution: Record<string, number>;
  average_exposure: number;
  concentration: number; // HHI
  last_updated: string;
}

export interface BulkOperation {
  type: 'update' | 'delete' | 'export';
  holding_ids: string[];
  updates?: Partial<Holding>;
}

export interface HoldingFilters {
  search?: string;
  sectors?: string[];
  ratings?: string[];
  currencies?: string[];
  exposure_min?: number;
  exposure_max?: number;
}

export interface HoldingSortConfig {
  field: keyof Holding;
  direction: 'asc' | 'desc';
}