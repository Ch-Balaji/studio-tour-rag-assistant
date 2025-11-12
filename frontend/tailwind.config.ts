import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Soft Blue-Gray Theme (Easy on Eyes)
        background: 'rgb(15, 23, 42)',        // Slate-900 - Soft dark blue-gray
        card: 'rgb(30, 41, 59)',              // Slate-800 - Card background
        'card-hover': 'rgb(51, 65, 85)',     // Slate-700 - Card hover
        border: 'rgb(51, 65, 85)',            // Slate-700 - Borders
        primary: 'rgb(59, 130, 246)',         // Blue-500 - Primary accent
        'primary-hover': 'rgb(37, 99, 235)',  // Blue-600 - Primary hover
        'primary-dark': 'rgb(29, 78, 216)',   // Blue-700 - Darker for glows
        foreground: 'rgb(248, 250, 252)',    // Slate-50 - Main text (soft white)
        'foreground-muted': 'rgb(148, 163, 184)', // Slate-400 - Muted text
        secondary: 'rgb(30, 41, 59)',         // Slate-800 - Secondary backgrounds
        accent: 'rgb(51, 65, 85)',            // Slate-700 - Accents
        // User message color (light green - kept as requested)
        'user-message': 'rgb(74, 222, 128)',  // Light green for user bubbles
        'user-message-text': 'rgb(0, 0, 0)',   // Black text for user messages
        // Assistant message color (soft dark blue-gray)
        'assistant-message': 'rgb(30, 41, 59)', // Slate-800 for assistant bubbles
      },
      typography: (theme: any) => ({
        DEFAULT: {
          css: {
            maxWidth: 'none',
            color: theme('colors.foreground'),
            a: {
              color: theme('colors.primary'),
              '&:hover': {
                color: theme('colors.primary-hover'),
              },
            },
            code: {
              color: theme('colors.primary'),
              backgroundColor: theme('colors.card'),
              padding: '0.2em 0.4em',
              borderRadius: '0.25rem',
              fontWeight: '400',
            },
            'code::before': {
              content: '""',
            },
            'code::after': {
              content: '""',
            },
            strong: {
              color: theme('colors.foreground'),
              fontWeight: '700',
            },
            'strong code': {
              color: theme('colors.primary'),
            },
          },
        },
      }),
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
}
export default config


