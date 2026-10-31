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
        blue: {
          50: '#effbf9',
          100: '#d9f3ef',
          200: '#b4e6df',
          300: '#75d1c5',
          400: '#3eaa9f',
          500: '#17867b',
          600: '#00685f',
          700: '#00564e',
          800: '#064743',
          900: '#0c3835',
          950: '#062e2a',
        },
        navy: {
          50: '#f0f4f9',
          100: '#e1e9f2',
          200: '#c3d3e6',
          300: '#94b3d3',
          400: '#5e8ebe',
          500: '#386fa8',
          600: '#28568c',
          700: '#204571',
          800: '#30455a',
          900: '#213145',
          950: '#17283b',
        },
        canvas: '#f8f9ff',
        'surface-container': '#eff4ff',
        'surface-container-high': '#e5eeff',
        'ink': '#0b1c30',
        'ink-muted': '#3d4947',
        'outline-soft': '#d6e1f2',
        'sidebar': '#213145',
        'brand-teal': '#00685f',
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
        'fintech': '0 2px 8px rgba(11, 28, 48, 0.05)',
        'fintech-lg': '0 8px 24px rgba(11, 28, 48, 0.08)',
        'glow-safe': '0 0 15px rgba(16, 185, 129, 0.35)',
        'glow-medium': '0 0 15px rgba(245, 158, 11, 0.35)',
        'glow-high': '0 0 20px rgba(239, 68, 68, 0.45)',
      }
    },
  },
  plugins: [],
}
