/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        hub: {
          bg:       '#0b0b14',
          surface:  '#111122',
          card:     '#16162a',
          border:   '#232340',
          muted:    '#2a2a4a',
          primary:  '#7c3aed',
          'primary-hover': '#6d28d9',
          secondary:'#4f46e5',
          accent:   '#06b6d4',
          success:  '#10b981',
          warning:  '#f59e0b',
          error:    '#ef4444',
          'text-primary':   '#e2e8f0',
          'text-secondary': '#94a3b8',
          'text-muted':     '#475569',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      animation: {
        'fade-in': 'fadeIn 0.2s ease-out',
        'slide-in': 'slideIn 0.25s ease-out',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0', transform: 'translateY(4px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideIn: {
          '0%': { opacity: '0', transform: 'translateX(-8px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
      },
    },
  },
  plugins: [],
}
