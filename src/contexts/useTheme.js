import { createContext, useContext } from 'react';

// Kept apart from ThemeProvider: a file that exports only components keeps Vite's Fast Refresh working
export const ThemeContext = createContext();

export const useTheme = () => useContext(ThemeContext);
