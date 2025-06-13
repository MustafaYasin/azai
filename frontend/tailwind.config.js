/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['var(--font-geist-sans)', 'system-ui', 'sans-serif'],
        mono: ['var(--font-geist-mono)', 'monospace'],
        poppins: ['Poppins', 'sans-serif'],
      },
      colors: {
        'dark-primary': '#0a0a0b',
        'dark-secondary': '#1a1a1c',
        'dark-tertiary': '#2d2d30',
      },
    },
  },
  plugins: [],
}