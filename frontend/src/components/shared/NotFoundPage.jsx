import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

const POPULAR_PAGES = [
  { to: '/', label: 'Overview Dashboard' },
  { to: '/portfolio-analytics', label: 'Portfolio Analytics' },
  { to: '/interactive', label: 'Interactive Analytics' },
  { to: '/regulatory', label: 'Regulatory Reporting' },
  { to: '/financial-risk', label: 'Financial Risk (ECL/PCAF)' },
  { to: '/carbon', label: 'Carbon Credits' },
  { to: '/data-intake', label: 'Data Intake' },
  { to: '/climate-risk', label: 'Climate Risk Engine' },
];

export default function NotFoundPage() {
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] px-4">
      <div className="text-6xl font-bold text-gray-200 mb-2">404</div>
      <h1 className="text-xl font-semibold text-gray-800 mb-1">Page not found</h1>
      <p className="text-sm text-gray-500 mb-6">
        <code className="bg-gray-100 px-2 py-0.5 rounded text-xs">{location.pathname}</code> doesn't exist.
      </p>

      <div className="flex gap-3 mb-8">
        <button
          onClick={() => navigate(-1)}
          className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
        >
          Go Back
        </button>
        <button
          onClick={() => navigate('/')}
          className="px-4 py-2 text-sm font-medium text-white bg-emerald-600 rounded-md hover:bg-emerald-700"
        >
          Go to Dashboard
        </button>
      </div>

      <div className="w-full max-w-md">
        <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Popular pages</h2>
        <div className="grid grid-cols-2 gap-2">
          {POPULAR_PAGES.map(({ to, label }) => (
            <button
              key={to}
              onClick={() => navigate(to)}
              className="text-left px-3 py-2 text-sm text-gray-600 bg-gray-50 rounded-md hover:bg-emerald-50 hover:text-emerald-700 transition-colors"
            >
              {label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
