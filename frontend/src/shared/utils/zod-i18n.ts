import type { TFunction } from "i18next";
import type { ZodErrorMap } from "zod";

export function makeZodI18nMap(t: TFunction): ZodErrorMap {
  return (issue) => {
    switch (issue.code) {
      case "invalid_type":
        if (issue.received === "undefined") {
          return { message: t("form.errors.required") };
        }
        return { message: t("form.errors.invalid_type") };
      case "invalid_string":
        if (issue.validation === "email") {
          return { message: t("form.errors.email") };
        }
        return { message: t("form.errors.invalid_string") };
      case "too_small":
        return {
          message: t("form.errors.minLength", { count: issue.minimum as number }),
        };
      case "too_big":
        return {
          message: t("form.errors.maxLength", { count: issue.maximum as number }),
        };
      default:
        return { message: t("form.errors.required") };
    }
  };
}
