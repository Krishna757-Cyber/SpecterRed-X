/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        obsidian: '#080B12',
        navy: '#0D1220',
        surface: '#131A29',
        cyan: { DEFAULT: '#00D9FF' },
        violet: { DEFAULT: '#7047FF' },
        intel: '#9B7CFF',
        red: { agent: '#FF304F' },
        blue: { agent: '#278BFF' },
        success: '#29D391',
        warning: '#FFB547',
        ink: '#F4F7FC',
        muted: '#A8B3C7',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
      },
      borderRadius: {
        panel: '16px',
      },
      boxShadow: {
        glass: '0 8px 32px rgba(0, 0, 0, 0.37)',
        glow: '0 0 24px rgba(0, 217, 255, 0.25)',
        'glow-red': '0 0 24px rgba(255, 48, 79, 0.25)',
        'glow-blue': '0 0 24px rgba(39, 139, 255, 0.25)',
      },
      transitionDuration: {
        150: '150ms',
        250: '250ms',
        400: '400ms',
      },
      keyframes: {
        'fade-in': {
          '0%': { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'pulse-ring': {
          '0%, 100%': { opacity: '0.4' },
          '50%': { opacity: '1' },
        },
      },
      animation: {
        'fade-in': 'fade-in 400ms ease-out',
        'pulse-ring': 'pulse-ring 2.4s ease-in-out infinite',
      },
    },
  },
  plugins: [],
}
