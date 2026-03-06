/**
 * useScenarioTemplates — template library management.
 * Provides search, filter, and selection of official NGFS + custom templates.
 */
import { useState, useMemo, useCallback } from 'react';
import { SCENARIO_TEMPLATES, NGFS_FAMILIES } from '../data/ngfsData';

export function useScenarioTemplates() {
  const [searchQuery, setSearchQuery]       = useState('');
  const [selectedFamily, setSelectedFamily] = useState('all');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedTag, setSelectedTag]       = useState('all');
  const [sortBy, setSortBy]                 = useState('usage'); // 'usage' | 'name' | 'date'

  // Derived: all unique tags
  const allTags = useMemo(() => {
    const tags = new Set();
    SCENARIO_TEMPLATES.forEach(t => t.tags.forEach(tag => tags.add(tag)));
    return Array.from(tags).sort();
  }, []);

  // Derived: filtered + sorted templates
  const filtered = useMemo(() => {
    let list = [...SCENARIO_TEMPLATES];

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      list = list.filter(t =>
        t.name.toLowerCase().includes(q) ||
        t.description.toLowerCase().includes(q) ||
        t.tags.some(tag => tag.toLowerCase().includes(q))
      );
    }

    if (selectedFamily !== 'all') {
      list = list.filter(t => t.ngfsFamily === selectedFamily);
    }

    if (selectedCategory !== 'all') {
      list = list.filter(t => t.category === selectedCategory);
    }

    if (selectedTag !== 'all') {
      list = list.filter(t => t.tags.includes(selectedTag));
    }

    list.sort((a, b) => {
      if (sortBy === 'usage') return b.usageCount - a.usageCount;
      if (sortBy === 'name')  return a.name.localeCompare(b.name);
      if (sortBy === 'date')  return new Date(b.createdAt) - new Date(a.createdAt);
      return 0;
    });

    return list;
  }, [searchQuery, selectedFamily, selectedCategory, selectedTag, sortBy]);

  // Group by category for gallery display
  const grouped = useMemo(() => {
    const groups = {};
    filtered.forEach(t => {
      const key = t.category;
      if (!groups[key]) groups[key] = [];
      groups[key].push(t);
    });
    return groups;
  }, [filtered]);

  const getTemplate = useCallback((id) => SCENARIO_TEMPLATES.find(t => t.id === id) || null, []);

  const clearFilters = useCallback(() => {
    setSearchQuery('');
    setSelectedFamily('all');
    setSelectedCategory('all');
    setSelectedTag('all');
    setSortBy('usage');
  }, []);

  return {
    // State
    searchQuery,
    selectedFamily,
    selectedCategory,
    selectedTag,
    sortBy,
    // Data
    allTemplates:  SCENARIO_TEMPLATES,
    filtered,
    grouped,
    allTags,
    allFamilies:   ['all', ...NGFS_FAMILIES],
    allCategories: ['all', 'ngfs', 'custom', 'stress', 'regulatory'],
    // Actions
    setSearchQuery,
    setSelectedFamily,
    setSelectedCategory,
    setSelectedTag,
    setSortBy,
    getTemplate,
    clearFilters,
  };
}
