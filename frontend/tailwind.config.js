/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          bg:    '#F0F7FF',
          bg2:   '#E1EFFF',
          text:  '#0F2744',
          muted: '#4A6FA5',
          light: '#94B8D8',
        },
      },
      fontFamily: {
        sans:    ['"Noto Sans KR"', 'Nunito', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        display: ['Nunito', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        card:      '0 8px 32px rgba(14,165,233,0.10)',
        'card-lg': '0 16px 48px rgba(14,165,233,0.16)',
      },
      keyframes: {
        blob: {
          from: { transform: 'translate(0,0) scale(1)' },
          to:   { transform: 'translate(30px,25px) scale(1.07)' },
        },
      },
      animation: {
        blob: 'blob 14s ease-in-out infinite alternate',
      },
    },
  },
  plugins: [],
};
