import type { Config } from "tailwindcss";
const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0b2239",
        snow: { 50: "#f4f9fd", 100: "#e6f1fa", 200: "#cde3f4", 500: "#2b8bd6", 600: "#1b6fb5", 700: "#155791" },
        wa: { DEFAULT: "#25d366", dark: "#128c4a" },
      },
    },
  },
  plugins: [],
};
export default config;
