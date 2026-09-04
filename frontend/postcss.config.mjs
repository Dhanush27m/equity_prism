// Component: Frontend -> Build config -> PostCSS
// Belongs to: run by Next.js's build pipeline to process globals.css.
// Purpose: enables the Tailwind CSS v4 PostCSS plugin — this is the entire Tailwind
// build wiring (v4 no longer needs a separate tailwind.config.js for basic setup).

const config = {
  plugins: {
    "@tailwindcss/postcss": {},
  },
};

export default config;
