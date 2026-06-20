import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import LanguageDetector from "i18next-browser-languagedetector";

import fr from "./locales/fr.json";
import ar from "./locales/ar.json";

const RTL_LANGS = ["ar"];

function setDocumentDirection(lng: string) {
  const dir = RTL_LANGS.includes(lng) ? "rtl" : "ltr";
  document.documentElement.dir = dir;
  document.documentElement.lang = lng;
}

const detected = localStorage.getItem("i18nextLng") || "fr";
setDocumentDirection(detected);

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: {
      fr: { translation: fr },
      ar: { translation: ar },
    },
    fallbackLng: "fr",
    interpolation: { escapeValue: false },
  });

i18n.on("languageChanged", (lng) => {
  setDocumentDirection(lng);
  document.body.style.direction = RTL_LANGS.includes(lng) ? "rtl" : "ltr";
});

export default i18n;
