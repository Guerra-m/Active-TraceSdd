import type { Config } from 'tailwindcss'

const config: Config = {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        // ── Design system — Material tokens (DESIGN.md / code.html) ──────────
        primary: '#162839',
        'on-primary': '#ffffff',
        'primary-container': '#2c3e50',
        'on-primary-container': '#96a9be',
        'inverse-primary': '#b5c8df',
        'primary-fixed': '#d1e4fb',
        'primary-fixed-dim': '#b5c8df',
        'on-primary-fixed': '#091d2e',
        'on-primary-fixed-variant': '#36485b',

        secondary: '#4b6076',
        'on-secondary': '#ffffff',
        'secondary-container': '#cce2fc',
        'on-secondary-container': '#50657b',
        'secondary-fixed': '#cfe5ff',
        'secondary-fixed-dim': '#b3c9e2',
        'on-secondary-fixed': '#051d30',
        'on-secondary-fixed-variant': '#34495e',

        tertiary: '#362308',
        'on-tertiary': '#ffffff',
        'tertiary-container': '#4e381c',
        'on-tertiary-container': '#c1a17d',
        'tertiary-fixed': '#ffddb7',
        'tertiary-fixed-dim': '#e3c19b',
        'on-tertiary-fixed': '#291802',
        'on-tertiary-fixed-variant': '#5a4225',

        error: '#ba1a1a',
        'on-error': '#ffffff',
        'error-container': '#ffdad6',
        'on-error-container': '#93000a',

        background: '#fbf9fa',
        'on-background': '#1b1c1d',

        'surface-dim': '#dbd9db',
        'surface-bright': '#fbf9fa',
        'surface-container-lowest': '#ffffff',
        'surface-container-low': '#f5f3f4',
        'surface-container': '#efedef',
        'surface-container-high': '#e9e8e9',
        'surface-container-highest': '#e4e2e3',
        'on-surface': '#1b1c1d',
        'on-surface-variant': '#43474c',
        'inverse-surface': '#303032',
        'inverse-on-surface': '#f2f0f2',
        'surface-variant': '#e4e2e3',
        'surface-tint': '#4e6073',

        outline: '#74777d',
        'outline-variant': '#c4c6cd',

        // ── Backward-compat aliases (existing components) ─────────────────────
        // surface.DEFAULT / surface.muted / surface.subtle
        surface: {
          DEFAULT: '#fbf9fa',
          muted: '#fbf9fa',
          subtle: '#f5f3f4',
        },
        // text.DEFAULT / text.muted / text.subtle
        text: {
          DEFAULT: '#1b1c1d',
          muted: '#43474c',
          subtle: '#74777d',
        },
        // brand → Teal (CTA / primary actions per DESIGN.md)
        brand: {
          50:  '#f0fdfa',
          100: '#ccfbf1',
          200: '#99f6e4',
          300: '#5eead4',
          400: '#2dd4bf',
          500: '#14b8a6',
          600: '#0d9488',
          700: '#0f766e',
          800: '#115e59',
          900: '#134e4a',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      borderRadius: {
        DEFAULT: '0.125rem',
        sm:  '0.125rem',
        md:  '0.25rem',
        lg:  '0.5rem',
        xl:  '0.75rem',
        full: '9999px',
      },
      fontSize: {
        'display-lg': ['30px', { lineHeight: '38px', letterSpacing: '-0.02em', fontWeight: '600' }],
        'headline-md': ['20px', { lineHeight: '28px', letterSpacing: '-0.01em', fontWeight: '600' }],
        'title-sm':  ['16px', { lineHeight: '24px', fontWeight: '500' }],
        'body-md':   ['14px', { lineHeight: '20px', fontWeight: '400' }],
        'body-sm':   ['13px', { lineHeight: '18px', fontWeight: '400' }],
        'label-caps':['11px', { lineHeight: '16px', letterSpacing: '0.05em', fontWeight: '700' }],
        'data-mono': ['12px', { lineHeight: '16px', fontWeight: '400' }],
      },
    },
  },
  plugins: [],
}

export default config
