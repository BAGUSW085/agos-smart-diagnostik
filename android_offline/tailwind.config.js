/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    './www/**/*.html',
    './www/js/**/*.js'
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f0f7ff',
          100: '#e0effe',
          300: '#7dd3fc',
          400: '#38bdf8',
          500: '#0284c7',
          600: '#0369a1',
          700: '#075985',
          800: '#0c4a6e',
          900: '#0f172a',
          950: '#082f49'
        },
        accent: {
          400: '#f59e0b',
          500: '#d97706',
          600: '#b45309'
        }
      }
    }
  },
  plugins: []
};
