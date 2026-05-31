import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        slate: {
          25: "#f9fafb",
        },
      },
    },
  },
  plugins: [],
} satisfies Config;
