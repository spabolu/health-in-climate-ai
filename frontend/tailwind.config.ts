import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // HeatGuard Pro Safety Color Palette
        safety: {
          critical: '#DC2626', // Red-600 - Critical alerts, danger states
          warning: '#F59E0B',  // Amber-500 - Warning alerts, caution states
          safe: '#16A34A',     // Green-600 - Safe conditions, normal operations
          info: '#2563EB',     // Blue-600 - Information, data insights
        },
        // Extended color system for UI components
        background: 'var(--color-background)',
        foreground: 'var(--color-foreground)',
        card: {
          DEFAULT: 'hsl(var(--card))',
          foreground: 'hsl(var(--card-foreground))',
        },
        popover: {
          DEFAULT: 'hsl(var(--popover))',
          foreground: 'hsl(var(--popover-foreground))',
        },
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
        },
        secondary: {
          DEFAULT: 'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))',
        },
        muted: {
          DEFAULT: 'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))',
        },
        accent: {
          DEFAULT: 'hsl(var(--accent))',
          foreground: 'hsl(var(--accent-foreground))',
        },
        destructive: {
          DEFAULT: 'hsl(var(--destructive))',
          foreground: 'hsl(var(--destructive-foreground))',
        },
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Courier New', 'monospace'],
      },
      fontSize: {
        // Safety-critical typography scale
        'safety-xs': ['12px', { lineHeight: '16px', fontWeight: '500' }],
        'safety-sm': ['14px', { lineHeight: '20px', fontWeight: '500' }],
        'safety-base': ['16px', { lineHeight: '24px', fontWeight: '500' }],
        'safety-lg': ['18px', { lineHeight: '28px', fontWeight: '600' }],
        'safety-xl': ['20px', { lineHeight: '28px', fontWeight: '600' }],
        'safety-2xl': ['24px', { lineHeight: '32px', fontWeight: '700' }],
        'safety-3xl': ['32px', { lineHeight: '40px', fontWeight: '700' }],
      },
      spacing: {
        // HeatGuard Pro spacing system
        '18': '4.5rem',
        '88': '22rem',
      },
      borderRadius: {
        lg: '8px',
        md: '6px',
        sm: '4px',
      },
      animation: {
        // Safety-critical animations
        'pulse-critical': 'pulse 1s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'bounce-alert': 'bounce 1s infinite',
      },
      boxShadow: {
        // Safety-focused shadows
        'safety-sm': '0 1px 2px 0 rgb(0 0 0 / 0.05)',
        'safety': '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
        'safety-md': '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
        'safety-lg': '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
        'safety-critical': '0 0 0 2px #DC2626',
        'safety-warning': '0 0 0 2px #F59E0B',
        'safety-safe': '0 0 0 2px #16A34A',
      },
    },
  },
  plugins: [require('tailwindcss-animate')],
} satisfies Config

export default config