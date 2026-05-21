import { useTranslation } from "react-i18next";

const LANGUAGES = [
  { code: "fr", label: "FR" },
  { code: "en", label: "EN" },
  { code: "ar", label: "AR" },
];

export function LanguageSwitcher() {
  const { i18n } = useTranslation();

  return (
    <div className="flex gap-1">
      {LANGUAGES.map(({ code, label }) => (
        <button
          key={code}
          onClick={() => i18n.changeLanguage(code)}
          className={`px-2 py-1 text-xs rounded-md transition-colors font-medium ${
            i18n.language === code || i18n.language?.startsWith(code)
              ? "bg-white/20 text-white"
              : "text-blue-300 hover:text-white hover:bg-white/10"
          }`}
        >
          {label}
        </button>
      ))}
    </div>
  );
}
