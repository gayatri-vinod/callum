import type { Config } from "tailwindcss";

export default {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: "var(--bg)",
        elevated: "var(--bg-elevated)",
        surface: "var(--surface)",
        border: "var(--border)",
        ink: "var(--text)",
        mute: "var(--text-muted)",
        faint: "var(--text-faint)",
        accent: "var(--accent)",
      },
      fontFamily: {
        sans: ["var(--font-sans)"],
        mono: ["var(--font-mono)"],
      },
      borderRadius: {
        mac: "12px",
        pill: "999px",
      },
      boxShadow: {
        glow: "0 0 80px var(--glow)",
        soft: "0 20px 60px rgba(0,0,0,0.45)",
      },
      keyframes: {
        fadeUp: {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        pulseSoft: {
          "0%, 100%": { opacity: "0.45" },
          "50%": { opacity: "0.9" },
        },
      },
      animation: {
        fadeUp: "fadeUp 0.5s ease-out both",
        pulseSoft: "pulseSoft 2.4s ease-in-out infinite",
      },
    },
  },
  plugins: [],
} satisfies Config;
