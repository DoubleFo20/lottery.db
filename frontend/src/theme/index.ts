export const theme = {
  colors: {
    text: '#6b6375',
    textHeading: '#08060d',
    background: '#ffffff',
    border: '#e5e4e7',
    accent: '#aa3bff',
    accentBg: 'rgba(170, 59, 255, 0.1)',
    darkText: '#9ca3af',
    darkTextHeading: '#f3f4f6',
    darkBackground: '#16171d',
    darkBorder: '#2e303a',
    darkAccent: '#c084fc',
    darkAccentBg: 'rgba(192, 132, 252, 0.15)',
  },
  fonts: {
    sans: "system-ui, 'Segoe UI', Roboto, sans-serif",
    heading: "system-ui, 'Segoe UI', Roboto, sans-serif",
    mono: 'ui-monospace, Consolas, monospace',
  },
  layout: {
    topbarHeight: '56px',
    sidebarWidth: '220px',
  },
  spacing: {
    xs: '4px',
    sm: '8px',
    md: '16px',
    lg: '24px',
    xl: '32px',
  },
  breakpoints: {
    mobile: 768,
  },
} as const
