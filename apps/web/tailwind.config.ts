/* eslint-disable @typescript-eslint/no-require-imports */

import type { Config } from 'tailwindcss';
import { fontFamily } from 'tailwindcss/defaultTheme';

const config = {
  darkMode: ['class'],
  content: [
    './pages/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './app/**/*.{ts,tsx}',
    './src/**/*.{ts,tsx}'
  ],
  theme: {
    container: {
      center: true,
      padding: '1rem'
    },
    screens: {
      sm: '640px',
      md: '768px',
      lg: '1024px',
      xl: '1280px'
    },
    fontFamily: {
      sans: ['var(--font-easybooker)', ...fontFamily.sans],
      mono: ['var(--font-mono)', ...fontFamily.mono],
      heading: ['var(--font-circular)', ...fontFamily.sans]
    },
    fontSize: {
      xs: '0.75rem', // 12px
      sm: '0.875rem', // 14px
      base: '1rem', // 16px
      lg: '1.125rem', // 18px
      xl: '1.25rem', // 20px
      '2xl': '1.5rem', // 24px
      '3xl': '1.75rem', // 28px
      '4xl': '2rem', // 32px
      '5xl': '2.25rem', // 36px
      '6xl': '2.5rem', // 40px
      '7xl': '2.75rem', // 44px
      '8xl': '3.25rem' // 52px
    },
    lineHeight: {
      4: '1rem', // 16px
      5: '1.25rem', // 20px
      6: '1.5rem', // 24px
      7: '1.75rem', // 28px
      8: '2rem', // 32px
      9: '2.25rem', // 36px
      10: '2.5rem', // 40px
      11: '2.75rem', // 44px
      12: '3rem', // 48px
      13: '3.25rem', // 52px
      14: '3.5rem', // 56px
      15: '3.75rem', // 60px
      16: '4rem' // 64px
    },
    extend: {
      ringWidth: {
        10: '10px',
        12: '12px'
      },
      colors: {
        background: {
          primary: {
            DEFAULT: 'hsl(var(--background-primary) / <alpha-value>)'
          },
          secondary: {
            DEFAULT: 'hsl(var(--background-secondary) / <alpha-value>)'
          },
          tertiary: {
            DEFAULT: 'hsl(var(--background-tertiary) / <alpha-value>)'
          }
        },
        text: {
          primary: {
            DEFAULT: 'hsl(var(--text-primary) / <alpha-value>)',
            hover: 'hsl(var(--text-primary-hover) / <alpha-value>)',
            active: 'hsl(var(--text-primary-active) / <alpha-value>)',
            onFill: 'hsl(var(--text-primary-on-fill) / <alpha-value>)'
          },
          secondary: {
            DEFAULT: 'hsl(var(--text-secondary) / <alpha-value>)',
            hover: 'hsl(var(--text-secondary-hover) / <alpha-value>)',
            active: 'hsl(var(--text-secondary-active) / <alpha-value>)',
            onFill: 'hsl(var(--text-secondary-on-fill) / <alpha-value>)'
          },
          brand: {
            DEFAULT: 'hsl(var(--text-brand) / <alpha-value>)',
            hover: 'hsl(var(--text-brand-hover) / <alpha-value>)',
            active: 'hsl(var(--text-brand-active) / <alpha-value>)',
            onFill: 'hsl(var(--text-brand-on-fill) / <alpha-value>)'
          },
          bold: {
            DEFAULT: 'hsl(var(--text-bold) / <alpha-value>)',
            hover: 'hsl(var(--text-bold-hover) / <alpha-value>)',
            active: 'hsl(var(--text-bold-active) / <alpha-value>)',
            onFill: 'hsl(var(--text-bold-on-fill) / <alpha-value>)'
          },
          danger: {
            DEFAULT: 'hsl(var(--text-danger) / <alpha-value>)',
            hover: 'hsl(var(--text-danger-hover) / <alpha-value>)',
            active: 'hsl(var(--text-danger-active) / <alpha-value>)',
            onFill: 'hsl(var(--text-danger-on-fill) / <alpha-value>)'
          },
          info: {
            DEFAULT: 'hsl(var(--text-info) / <alpha-value>)',
            onFill: 'hsl(var(--text-info-on-fill) / <alpha-value>)'
          },
          success: {
            DEFAULT: 'hsl(var(--text-success) / <alpha-value>)',
            onFill: 'hsl(var(--text-success-on-fill) / <alpha-value>)'
          },
          critical: {
            DEFAULT: 'hsl(var(--text-danger) / <alpha-value>)',
            onFill: 'hsl(var(--text-danger-on-fill) / <alpha-value>)'
          },
          warning: {
            DEFAULT: 'hsl(var(--text-warning) / <alpha-value>)',
            hover: 'hsl(var(--text-warning-hover) / <alpha-value>)',
            active: 'hsl(var(--text-warning-active) / <alpha-value>)',
            onFill: 'hsl(var(--text-warning-on-fill) / <alpha-value>)'
          }
        },
        surface: {
          primary: {
            DEFAULT: 'hsl(var(--surface-primary) / <alpha-value>)',
            hover: 'hsl(var(--surface-primary-hover) / <alpha-value>)',
            active: 'hsl(var(--surface-primary-active) / <alpha-value>)',
            selected: 'hsl(var(--surface-primary-selected) / <alpha-value>)'
          },
          secondary: {
            DEFAULT: 'hsl(var(--surface-secondary) / <alpha-value>)'
          },
          tertiary: {
            DEFAULT: 'hsl(var(--surface-tertiary) / <alpha-value>)'
          },
          info: {
            DEFAULT: 'hsl(var(--surface-info) / <alpha-value>)'
          },
          success: {
            DEFAULT: 'hsl(var(--surface-success) / <alpha-value>)'
          },
          warning: {
            DEFAULT: 'hsl(var(--surface-warning) / <alpha-value>)'
          },
          danger: {
            DEFAULT: 'hsl(var(--surface-danger) / <alpha-value>)'
          },
          bold: {
            DEFAULT: 'hsl(var(--surface-bold) / <alpha-value>)'
          }
        },
        fill: {
          primary: {
            DEFAULT: 'hsl(var(--fill-primary) / <alpha-value>)',
            hover: 'hsl(var(--fill-primary-hover) / <alpha-value>)',
            active: 'hsl(var(--fill-primary-active) / <alpha-value>)',
            selected: 'hsl(var(--fill-primary-selected) / <alpha-value>)'
          },
          secondary: {
            DEFAULT: 'hsl(var(--fill-secondary) / <alpha-value>)',
            hover: 'hsl(var(--fill-secondary-hover) / <alpha-value>)',
            active: 'hsl(var(--fill-secondary-active) / <alpha-value>)',
            selected: 'hsl(var(--fill-secondary-selected) / <alpha-value>)'
          },
          brand: {
            DEFAULT: 'hsl(var(--fill-brand) / <alpha-value>)',
            hover: 'hsl(var(--fill-brand-hover) / <alpha-value>)',
            active: 'hsl(var(--fill-brand-active) / <alpha-value>)',
            selected: 'hsl(var(--fill-brand-selected) / <alpha-value>)'
          },
          bold: {
            DEFAULT: 'hsl(var(--fill-bold) / <alpha-value>)',
            hover: 'hsl(var(--fill-bold-hover) / <alpha-value>)',
            active: 'hsl(var(--fill-bold-active) / <alpha-value>)',
            selected: 'hsl(var(--fill-bold-selected) / <alpha-value>)'
          },
          danger: {
            DEFAULT: 'hsl(var(--fill-danger) / <alpha-value>)',
            hover: 'hsl(var(--fill-danger-hover) / <alpha-value>)',
            active: 'hsl(var(--fill-danger-active) / <alpha-value>)',
            selected: 'hsl(var(--fill-danger-selected) / <alpha-value>)'
          },
          info: {
            DEFAULT: 'hsl(var(--fill-info) / <alpha-value>)'
          },
          success: {
            DEFAULT: 'hsl(var(--fill-success) / <alpha-value>)',
            hover: 'hsl(var(--fill-success-hover) / <alpha-value>)',
            active: 'hsl(var(--fill-success-active) / <alpha-value>)',
            selected: 'hsl(var(--fill-success-selected) / <alpha-value>)',
            onFill: 'hsl(var(--fill-success-on-fill) / <alpha-value>)'
          },
          critical: {
            DEFAULT: 'hsl(var(--fill-danger) / <alpha-value>)',
            hover: 'hsl(var(--fill-danger-hover) / <alpha-value>)',
            active: 'hsl(var(--fill-danger-active) / <alpha-value>)',
            selected: 'hsl(var(--fill-danger-selected) / <alpha-value>)'
          },
          warning: {
            DEFAULT: 'hsl(var(--fill-warning) / <alpha-value>)'
          }
        },
        border: {
          primary: {
            DEFAULT: 'hsl(var(--border-primary) / <alpha-value>)',
            hover: 'hsl(var(--border-primary-hover) / <alpha-value>)',
            active: 'hsl(var(--border-primary-active) / <alpha-value>)',
            selected: 'hsl(var(--border-primary-selected) / <alpha-value>)'
          },
          secondary: {
            DEFAULT: 'hsl(var(--border-secondary) / <alpha-value>)',
            hover: 'hsl(var(--border-secondary-hover) / <alpha-value>)',
            active: 'hsl(var(--border-secondary-active) / <alpha-value>)',
            selected: 'hsl(var(--border-secondary-selected) / <alpha-value>)'
          },
          brand: {
            DEFAULT: 'hsl(var(--border-brand) / <alpha-value>)',
            hover: 'hsl(var(--border-brand-hover) / <alpha-value>)',
            active: 'hsl(var(--border-brand-active) / <alpha-value>)',
            selected: 'hsl(var(--border-brand-selected) / <alpha-value>)'
          },
          info: {
            DEFAULT: 'hsl(var(--border-info) / <alpha-value>)',
            hover: 'hsl(var(--border-info-hover) / <alpha-value>)',
            active: 'hsl(var(--border-info-active) / <alpha-value>)',
            selected: 'hsl(var(--border-info-selected) / <alpha-value>)'
          },
          danger: {
            DEFAULT: 'hsl(var(--border-danger) / <alpha-value>)',
            hover: 'hsl(var(--border-danger-hover) / <alpha-value>)',
            active: 'hsl(var(--border-danger-active) / <alpha-value>)',
            selected: 'hsl(var(--border-danger-selected) / <alpha-value>)'
          }
        }
      },
      keyframes: {
        marquee: {
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(0)' }
        },
        'marquee-reverse': {
          '0%': { transform: 'translateX(0)' },
          '100%': { transform: 'translateX(-100%)' }
        },
        'marquee-reverse-2': {
          '0%': { transform: 'translateX(100%)' },
          '100%': { transform: 'translateX(0)' }
        },
        'accordion-down': {
          from: { height: '0' },
          to: {
            height: 'hsl(var(--radix-accordion-content-height) / <alpha-value>)'
          }
        },
        'accordion-up': {
          from: {
            height: 'hsl(var(--radix-accordion-content-height) / <alpha-value>)'
          },
          to: { height: '0' }
        }
      },
      animation: {
        'accordion-down': 'accordion-down 0.2s ease-out',
        'accordion-up': 'accordion-up 0.2s ease-out',
        marquee: 'marquee 60s linear infinite',
        'marquee-reverse': 'marquee-reverse 60s linear infinite'
      },
      backgroundImage: () => ({
        'gradient-brand-light': `linear-gradient(45deg, hsl(230, 50%, 97%) 0%, hsl(230, 50%, 95%) 20%, hsl(230, 50%, 97%) 40%, hsl(230, 50%, 95%) 60%, hsl(230, 50%, 97%) 80%, hsl(230, 50%, 95%) 100%)`,
        'gradient-brand': `linear-gradient(45deg, hsl(21, 97%, 55%) 0%, hsl(21, 97%, 66%) 100%)`
      }),
      typography: () => ({
        DEFAULT: {
          css: {
            '--tw-prose-body': 'inherit',
            '--tw-prose-headings': 'inherit',
            '--tw-prose-lead': 'inherit',
            '--tw-prose-links': 'inherit',
            '--tw-prose-bold': 'inherit',
            '--tw-prose-counters': 'inherit',
            '--tw-prose-bullets': 'inherit',
            '--tw-prose-hr': 'inherit',
            '--tw-prose-quotes': 'var(--text-secondary)',
            '--tw-prose-quote-borders': 'var(--border-primary)',
            '--tw-prose-captions': 'inherit',
            '--tw-prose-code': 'inherit',
            '--tw-prose-pre-code': 'inherit',
            '--tw-prose-pre-bg': 'inherit',
            '--tw-prose-th-borders': 'inherit',
            '--tw-prose-td-borders': 'inherit',
            '--tw-prose-kbd': 'inherit',
            '--tw-prose-kbd-shadows': 'inherit',
            '--tw-prose-invert-body': 'inherit',
            '--tw-prose-invert-headings': 'inherit',
            '--tw-prose-invert-lead': 'inherit',
            '--tw-prose-invert-links': 'inherit',
            '--tw-prose-invert-bold': 'inherit',
            '--tw-prose-invert-counters': 'inherit',
            '--tw-prose-invert-bullets': 'inherit',
            '--tw-prose-invert-hr': 'inherit',
            '--tw-prose-invert-quotes': 'inherit',
            '--tw-prose-invert-quote-borders': 'inherit',
            '--tw-prose-invert-captions': 'inherit',
            '--tw-prose-invert-code': 'inherit',
            '--tw-prose-invert-pre-code': 'inherit',
            '--tw-prose-invert-pre-bg': 'inherit',
            '--tw-prose-invert-th-borders': 'inherit',
            '--tw-prose-invert-td-borders': 'inherit',
            '--tw-prose-invert-kbd': 'inherit',
            '--tw-prose-invert-kbd-shadows': 'inherit'
          }
        }
      }),
    }
  },
  plugins: [require('@tailwindcss/typography'), require('tailwindcss-animate')]
} satisfies Config;

export default config;
