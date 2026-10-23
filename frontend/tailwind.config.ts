import type { Config } from "tailwindcss";

const token = (name: string) => `rgb(var(--${name}) / <alpha-value>)`;

const config: Config = {
  darkMode: ["selector", '[data-theme="dark"]'],
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./hooks/**/*.{ts,tsx}"],
  theme: {
    container: { center: true, padding: "1rem", screens: { "2xl": "1200px" } },
    extend: {
      // Uniwise design system colour tokens (see app/globals.css)
      colors: {
        paper: token("paper"),
        "paper-raised": token("paper-raised"),
        "paper-sunk": token("paper-sunk"),
        line: token("line"),
        "line-strong": token("line-strong"),
        ink: token("ink"),
        "ink-muted": token("ink-muted"),
        blue: token("blue"),
        "blue-soft": token("blue-soft"),
        "on-blue": token("on-blue"),
        amber: token("amber"),
        "amber-ink": token("amber-ink"),
        "amber-soft": token("amber-soft"),
        red: token("red"),
        "red-soft": token("red-soft"),
        "on-red": token("on-red"),
      },
      fontFamily: {
        serif: ["var(--font-newsreader)", "Georgia", "serif"],
        sans: ["var(--font-be-vietnam)", "Segoe UI", "system-ui", "sans-serif"],
        mono: ["var(--font-plex-mono)", "ui-monospace", "Consolas", "monospace"],
      },
      fontSize: {
        // Modular scale ~1.25, line-heights tuned for Vietnamese diacritics
        xs: ["0.75rem", { lineHeight: "1.1rem" }],
        sm: ["0.875rem", { lineHeight: "1.35rem" }],
        base: ["1rem", { lineHeight: "1.6rem" }],
        lg: ["1.25rem", { lineHeight: "1.8rem" }],
        xl: ["1.563rem", { lineHeight: "2.1rem" }],
        "2xl": ["1.953rem", { lineHeight: "2.5rem" }],
        "3xl": ["2.441rem", { lineHeight: "3rem" }],
        "4xl": ["3.052rem", { lineHeight: "3.6rem" }],
      },
      // Small and precise: xs bars, sm inputs/badges, DEFAULT/md/lg buttons and cards
      borderRadius: { xs: "2px", sm: "4px", DEFAULT: "6px", md: "6px", lg: "6px" },
      maxWidth: { prose: "68ch" },
    },
  },
  plugins: [],
};

export default config;
