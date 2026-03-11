import enUS from "./en-US";
import zhCN from "./zh-CN";


export type LocaleCode = "en-US" | "zh-CN";
type LocaleValue = string | LocaleTree;
type LocaleTree = Record<string, LocaleValue>;

export const DEFAULT_LOCALE: LocaleCode = "en-US";

export const SUPPORTED_LOCALES: Array<{ code: LocaleCode; nativeLabel: string }> = [
  { code: "en-US", nativeLabel: "English" },
  { code: "zh-CN", nativeLabel: "简体中文" },
];

const LOCALE_MESSAGES: Record<LocaleCode, LocaleTree> = {
  "en-US": enUS,
  "zh-CN": zhCN,
};

export function isLocaleCode(value: string | null | undefined): value is LocaleCode {
  return SUPPORTED_LOCALES.some((locale) => locale.code === value);
}

export function detectDefaultLocale(): LocaleCode {
  const envLocale = import.meta.env.VITE_DEFAULT_LOCALE;
  if (isLocaleCode(envLocale)) {
    return envLocale;
  }

  if (typeof navigator !== "undefined") {
    for (const language of navigator.languages ?? [navigator.language]) {
      if (language.toLowerCase().startsWith("zh")) {
        return "zh-CN";
      }
      if (language.toLowerCase().startsWith("en")) {
        return "en-US";
      }
    }
  }

  return DEFAULT_LOCALE;
}

function resolvePath(tree: LocaleTree, key: string): string | undefined {
  let current: LocaleValue | undefined = tree;

  for (const part of key.split(".")) {
    if (!current || typeof current === "string") {
      return undefined;
    }
    current = current[part];
  }

  return typeof current === "string" ? current : undefined;
}

function interpolate(message: string, params?: Record<string, string | number>): string {
  if (!params) {
    return message;
  }

  return message.replace(/\{(\w+)\}/g, (_match, key) => String(params[key] ?? `{${key}}`));
}

export function translate(
  locale: LocaleCode,
  key: string,
  params?: Record<string, string | number>,
): string {
  const message = resolvePath(LOCALE_MESSAGES[locale], key) ?? resolvePath(LOCALE_MESSAGES[DEFAULT_LOCALE], key) ?? key;
  return interpolate(message, params);
}
