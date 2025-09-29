/****************
 * Tailwind config
 ****************/
export default {
  content: [
    './index.html',
    './src/**/*.{vue,js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          violet: '#7c5cff',
          cyan: '#00d4ff',
          dark: '#0b0b11',
          soft: '#10111a',
        }
      },
      boxShadow: {
        soft: '0 10px 30px rgba(0,0,0,0.35)',
      },
      borderRadius: {
        '2xl': '1.25rem',
      },
    },
  },
  plugins: [],
}
