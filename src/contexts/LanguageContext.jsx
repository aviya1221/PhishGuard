import { useEffect, useState } from 'react';
import { LanguageContext } from './useLanguage';

const translations = {
  en: {
    appTitle: 'PhishGuard AI',
    appSubtitle: 'Secure your digital world with advanced AI protection.',
    dragDrop: 'Drag & drop your image here',
    orBrowse: 'or click to browse',
    supports: 'Supports PNG, JPG, JPEG',
    uploading: 'Uploading...',
    scanning: 'Scanning...',
    analyzingBranding: 'Analyzing Branding...',
    checkingUrls: 'Checking URLs...',
    evaluatingTone: 'Evaluating Tone...',
    clickDifferent: 'Click to upload a different image',
    privacyNotice: 'Privacy Notice',
    privacyText: 'Before uploading, please crop out any sensitive personal information (such as faces, addresses, or personal details) to protect your privacy.',
    verdictDesc: 'Phishing assessment based on AI analysis',
    reasoningReport: 'Reasoning Report',
    recommendation: 'Recommendation',
    disclaimer: 'This analysis is generated automatically by AI and is meant as guidance only. It may not be fully accurate and does not guarantee safety. Any decision or action you take is your own responsibility, and PhishGuard AI is not liable for its outcome. When in doubt, contact the organization directly through its official channels.',
    score: 'Score',
    safe: 'Safe',
    suspicious: 'Suspicious',
    phishing: 'Phishing',
    critical: 'Critical Phishing',
    analysisFailed: 'Analysis failed. Please try again or check your connection.',
    invalidFileType: 'Please upload a PNG, JPG, or JPEG file.',
    fileTooLarge: 'The file is too large. Maximum size is 10 MB.',
    tooManyRequests: 'Too many scans in a short time. Please wait a minute and try again.',
    analysisTimeout: 'The analysis took too long. Please try again.',
    cancel: 'Cancel'
  },
  he: {
    appTitle: 'PhishGuard AI',
    appSubtitle: 'שמור על העולם הדיגיטלי שלך עם הגנה מתקדמת מבוססת בינה מלאכותית.',
    dragDrop: 'גרור ושחרר את התמונה שלך כאן',
    orBrowse: 'או לחץ כדי לבחור תמונה מהמכשיר',
    supports: 'תומך בקבצים מסוג- PNG, JPG, JPEG',
    uploading: 'מעלה...',
    scanning: 'סורק...',
    analyzingBranding: 'מחפש זיופים ויזואליים...',
    checkingUrls: 'סורק קישורים חשודים...',
    evaluatingTone: 'סורק מניפולציות בטקסט...',
    clickDifferent: 'לחץ כדי להעלות תמונה אחרת',
    privacyNotice: 'הודעת פרטיות',
    privacyText: 'לפני ההעלאה, אנא חתוך מידע אישי רגיש (כגון: פנים, כתובות או פרטים אישיים) כדי להגן על הפרטיות שלך.',
    verdictDesc: 'הערכת סיכוני פישינג מבוססת על ניתוח AI',
    reasoningReport: 'דוח נימוקים',
    recommendation: 'המלצה',
    disclaimer: 'הניתוח מופק באופן אוטומטי על ידי בינה מלאכותית ונועד לסייע בלבד. ייתכן שאינו מדויק במלואו, והוא אינו מהווה ערובה לבטיחות. כל החלטה או פעולה בעקבותיו הן באחריותך, ו-PhishGuard AI אינה אחראית לתוצאותיהן. במקרה של ספק, מומלץ לפנות לגוף הרלוונטי ישירות דרך הערוצים הרשמיים שלו.',
    score: 'ציון',
    safe: 'בטוח',
    suspicious: 'חשוד',
    phishing: 'הונאה',
    critical: 'פישינג קריטי',
    analysisFailed: 'הניתוח נכשל. אנא נסה שוב או בדוק את החיבור שלך.',
    invalidFileType: 'יש להעלות קובץ מסוג PNG, JPG או JPEG.',
    fileTooLarge: 'הקובץ גדול מדי. הגודל המקסימלי הוא 10MB.',
    tooManyRequests: 'בוצעו יותר מדי סריקות בזמן קצר. אנא המתן דקה ונסה שוב.',
    analysisTimeout: 'הניתוח לקח יותר מדי זמן. אנא נסה שוב.',
    cancel: 'ביטול'
  }
};

export const LanguageProvider = ({ children }) => {
  const [language, setLanguage] = useState(() => {
    const saved = localStorage.getItem('language');
    return saved || 'en';
  });

  useEffect(() => {
    document.documentElement.dir = language === 'he' ? 'rtl' : 'ltr';
    localStorage.setItem('language', language);
  }, [language]);

  const toggleLanguage = () => setLanguage(language === 'en' ? 'he' : 'en');

  const t = (key) => translations[language][key] || key;

  return (
    <LanguageContext.Provider value={{ language, toggleLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  );
};