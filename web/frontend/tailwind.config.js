/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Lora', 'Georgia', 'serif'],
        mono: ['JetBrains Mono', 'monospace'],
        display: ['"Playfair Display"', 'serif'],
      },
      colors: {
        ink: {
          50:  '#f5f0eb', 100: '#e8ddd3', 200: '#d4c4b5',
          300: '#bba48f', 400: '#9e8068', 500: '#7d5f48',
          600: '#614838', 700: '#4a3629', 800: '#32251c',
          900: '#1c1410', 950: '#0e0a07',
        },
        blush: {
          100: '#fce8e4', 200: '#f8cfc8', 300: '#f0a89d',
          400: '#e47d6e', 500: '#d45a48',
        },
        sage: {
          100: '#e8ede6', 200: '#c8d6c3', 300: '#9ab893',
          400: '#6b9462', 500: '#4a7142',
        },
      },
      keyframes: {
        'fade-up': {
          '0%':   { opacity: '0', transform: 'translateY(12px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        blink: {
          '0%, 100%': { opacity: '1' },
          '50%':      { opacity: '0' },
        },
      },
      animation: {
        'fade-up': 'fade-up 0.4s ease-out',
        blink:     'blink 1s step-end infinite',
      },
    },
  },
  plugins: [],
}
