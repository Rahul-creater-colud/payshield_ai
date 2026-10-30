/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        navy: {
          50: '#f0f4f9',
          100: '#e1e9f2',
          200: '#c3d3e6',
          300: '#94b3d3',
          400: '#5e8ebe',
          500: '#386fa8',
          600: '#28568c',
          700: '#204571',
          800: '#1b3a5e',
          900: '#0f2038',
          950: '#081120',
        },
        risk: {
          safe: '#10b981',
          'safe-bg': '#ecfdf5',
          'safe-border': '#a7f3d0',
          medium: '#f59e0b',
          'medium-bg': '#fffbeb',
          'medium-border': '#fde68a',
          high: '#ef4444',
          'high-bg': '#fef2f2',
          'high-border': '#fecaca',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'Consolas', 'monospace']
      },
      boxShadow: {
        'fintech': '0 4px 20px -2px rgba(15, 32, 56, 0.08), 0 2px 6px -2px rgba(15, 32, 56, 0.04)',
        'fintech-lg': '0 10px 30px -4px rgba(15, 32, 56, 0.12), 0 4px 10px -2px rgba(15, 32, 56, 0.06)',
        'glow-safe': '0 0 15px rgba(16, 185, 129, 0.35)',
        'glow-medium': '0 0 15px rgba(245, 158, 11, 0.35)',
        'glow-high': '0 0 20px rgba(239, 68, 68, 0.45)',
      }
    },
  },
  plugins: [],
}
