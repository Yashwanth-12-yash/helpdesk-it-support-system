/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        navy: {
          900: "#0B162C",
          800: "#122344",
          700: "#1B335F",
        },
      },
    },
  },
  plugins: [],
};
