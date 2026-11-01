import { createContext, useContext } from 'react';

// Kept apart from LanguageProvider: a file that exports only components keeps Vite's Fast Refresh working
export const LanguageContext = createContext();

export const useLanguage = () => useContext(LanguageContext);
