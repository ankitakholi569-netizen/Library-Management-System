/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{js,jsx,ts,tsx,html}'],
  theme: {
    extend: {
      colors: {
        primaryBlue: '#2563EB',
        primaryGreen: '#10B981',
        primaryPurple: '#7C3AED',
        darkSlate: '#1E1E2D',
      },
      fontFamily: { sans: ['Inter', 'system-ui', 'sans-serif'] },
    },
  },
  plugins: [],
};

