/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Sector sentiment colors
        'sector-dark-red': '#dc2626',
        'sector-light-red': '#ef4444',
        'sector-blue-neutral': '#3b82f6',
        'sector-light-green': '#10b981',
        'sector-dark-green': '#059669',
        
        // Background colors
        'bg-primary': '#1f2937',
        'bg-secondary': '#374151',
        'bg-tertiary': '#4b5563',
        
        // Text colors
        'text-primary': '#f9fafb',
        'text-secondary': '#d1d5db',
        'text-accent': '#fbbf24',
        
        // Border colors
        'border-primary': '#6b7280',
        'border-secondary': '#4b5563',
      },
      
      // Custom animation for sector transitions
      animation: {
        'fade-in': 'fadeIn 0.3s ease-in-out',
        'slide-up': 'slideUp 0.2s ease-out',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}; 