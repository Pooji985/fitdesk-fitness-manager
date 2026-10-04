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
        gym: {
          dark: '#0f172a',
          surface: '#1e293b',
          card: '#162032',
          border: '#334155',
          accent: '#10b981', // Emerald green
          highlight: '#06b6d4', // Cyan
          warning: '#f59e0b',
          danger: '#ef4444',
        },
      },
    },
  },
  plugins: [],
};
