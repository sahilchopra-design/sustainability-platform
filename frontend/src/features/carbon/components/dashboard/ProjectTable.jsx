/**
 * ProjectTable Component
 * Displays carbon projects in a sortable table
 */

import React, { useState, useMemo } from 'react';
import { ArrowUpDown, MoreHorizontal, Eye, Pencil, Trash2 } from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '../../../../components/ui/dropdown-menu';
import { Button } from '../../../../components/ui/button';

export const ProjectTable = ({
  projects = [],
  onEdit,
  onDelete,
  onView
}) => {
  const [sortKey, setSortKey] = useState('name');
  const [sortOrder, setSortOrder] = useState('asc');

  const handleSort = (key) => {
    if (sortKey === key) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(key);
      setSortOrder('asc');
    }
  };

  const sortedProjects = useMemo(() => {
    return [...projects].sort((a, b) => {
      const aValue = a[sortKey];
      const bValue = b[sortKey];
      
      if (aValue === undefined || aValue === null) return 1;
      if (bValue === undefined || bValue === null) return -1;
      
      if (aValue < bValue) return sortOrder === 'asc' ? -1 : 1;
      if (aValue > bValue) return sortOrder === 'asc' ? 1 : -1;
      return 0;
    });
  }, [projects, sortKey, sortOrder]);

  const getQualityBadgeColor = (rating) => {
    switch (rating) {
      case 'AAA':
      case 'AA':
        return 'bg-emerald-100 text-emerald-300';
      case 'A':
        return 'bg-blue-100 text-blue-300';
      case 'BBB':
        return 'bg-amber-100 text-amber-300';
      default:
        return 'bg-white/[0.06] text-white/90';
    }
  };

  const getRiskBadgeColor = (level) => {
    switch (level?.toLowerCase()) {
      case 'low':
        return 'bg-emerald-100 text-emerald-300';
      case 'medium':
        return 'bg-amber-100 text-amber-300';
      case 'high':
        return 'bg-rose-100 text-rose-800';
      default:
        return 'bg-white/[0.06] text-white/90';
    }
  };

  const columns = [
    { key: 'name', label: 'Project Name' },
    { key: 'project_type', label: 'Type' },
    { key: 'standard', label: 'Standard' },
    { key: 'annual_credits', label: 'Annual Credits' },
    { key: 'quality_rating', label: 'Quality' },
    { key: 'risk_level', label: 'Risk' }
  ];

  return (
    <div className="bg-[#0d1424] rounded-xl border border-white/[0.06] overflow-hidden" data-testid="project-table">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-white/[0.02] border-b border-white/[0.06]">
            <tr>
              {columns.map((column) => (
                <th
                  key={column.key}
                  className="px-6 py-3 text-left text-xs font-semibold text-white/40 uppercase tracking-wider cursor-pointer hover:bg-white/[0.06] transition-colors"
                  onClick={() => handleSort(column.key)}
                >
                  <div className="flex items-center gap-1">
                    {column.label}
                    <ArrowUpDown className="w-3 h-3" />
                  </div>
                </th>
              ))}
              <th className="px-6 py-3 text-right text-xs font-semibold text-white/40 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200">
            {sortedProjects.map((project) => (
              <tr
                key={project.id}
                className="hover:bg-white/[0.02] transition-colors"
                data-testid={`project-row-${project.id}`}
              >
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm font-medium text-white">
                    {project.name}
                  </div>
                  <div className="text-xs text-white/40">
                    {project.country_code}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="text-sm text-white/70">
                    {project.project_type?.replace(/_/g, ' ')}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-300">
                    {project.standard}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-white tabular-nums">
                    {project.annual_credits?.toLocaleString()}
                  </div>
                  <div className="text-xs text-white/40">tCO2e/yr</div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getQualityBadgeColor(project.quality_rating)}`}>
                    {project.quality_rating || 'N/A'}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getRiskBadgeColor(project.risk_level)}`}>
                    {project.risk_level || 'N/A'}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                        <MoreHorizontal className="w-4 h-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem onClick={() => onView?.(project)}>
                        <Eye className="w-4 h-4 mr-2" />
                        View Details
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => onEdit?.(project)}>
                        <Pencil className="w-4 h-4 mr-2" />
                        Edit
                      </DropdownMenuItem>
                      <DropdownMenuItem 
                        onClick={() => onDelete?.(project)}
                        className="text-rose-400"
                      >
                        <Trash2 className="w-4 h-4 mr-2" />
                        Delete
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      
      {projects.length === 0 && (
        <div className="text-center py-12">
          <p className="text-white/40">No projects found</p>
          <button className="mt-2 text-blue-300 hover:text-blue-300 text-sm font-medium">
            Add your first project
          </button>
        </div>
      )}
    </div>
  );
};

export default ProjectTable;
