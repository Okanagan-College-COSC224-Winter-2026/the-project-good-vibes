/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        'text-primary': '#000000',
        'text-secondary': '#4d4d4d',
        'bg-primary': '#ffffff',
        'bg-secondary': '#dcdcdc',
        'bg-tertiary': '#b5b5b5',
        'btn-primary': '#4bd530',
        'btn-secondary': '#999999',
        'btn-disabled': '#4d4d4d',
      },
      fontFamily: {
        sans: ['Arial', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
