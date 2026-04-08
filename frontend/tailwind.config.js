/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#2563eb',
          hover: '#1d4ed8',
        },
      },
      fontFamily: {
        sans: ['Inter', 'PingFang SC', 'Microsoft YaHei', 'Noto Sans SC', 'sans-serif'],
      },
      boxShadow: {
        card: '0 1px 2px 0 rgb(15 23 42 / 0.08), 0 1px 1px -1px rgb(15 23 42 / 0.06)',
      },
    },
  },
  plugins: [],
};

