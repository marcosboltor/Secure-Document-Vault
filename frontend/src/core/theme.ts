export const theme = {
  dark: {
    bg: "#0a0a0a",
    bgCard: "#161616",
    text: "#e5e5e5",
    textDim: "#737373",
    primary: "#10b981",
    border: "#262626",
  },
  light: {
    bg: "#f5f5f5",
    bgCard: "#ffffff",
    text: "#171717",
    textDim: "#737373",
    primary: "#10b981",
    border: "#e5e5e5",
  },
} as const;

export type ThemeMode = keyof typeof theme;