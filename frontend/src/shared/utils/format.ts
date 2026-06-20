const LOCALE = "fr-DZ";

export const fmtDate = (d: string | null | undefined): string =>
  d ? new Date(d).toLocaleDateString(LOCALE, { day: "2-digit", month: "short", year: "numeric" }) : "—";

export const fmtDateTime = (d: string | null | undefined): string =>
  d ? new Date(d).toLocaleString(LOCALE, { day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" }) : "—";

export const fmtDateLong = (d: string | null | undefined): string =>
  d ? new Date(d).toLocaleDateString(LOCALE, { day: "2-digit", month: "long", year: "numeric" }) : "—";

export const fmtTime = (d: string | null | undefined): string =>
  d ? new Date(d).toLocaleTimeString(LOCALE, { hour: "2-digit", minute: "2-digit" }) : "—";
