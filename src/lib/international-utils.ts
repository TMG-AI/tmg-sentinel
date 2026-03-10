/** Utilities for international subject display */

const US_CODES = ["US", "USA", "UNITED STATES", "UNITED STATES OF AMERICA"];

export function isInternationalSubject(country: string | null | undefined): boolean {
  if (!country) return false;
  return !US_CODES.includes(country.toUpperCase().trim());
}

const COUNTRY_FLAGS: Record<string, string> = {
  "PAKISTAN": "🇵🇰",
  "INDIA": "🇮🇳",
  "UK": "🇬🇧",
  "UNITED KINGDOM": "🇬🇧",
  "GREAT BRITAIN": "🇬🇧",
  "NIGERIA": "🇳🇬",
  "CHINA": "🇨🇳",
  "RUSSIA": "🇷🇺",
  "SAUDI ARABIA": "🇸🇦",
  "JAPAN": "🇯🇵",
  "GERMANY": "🇩🇪",
  "FRANCE": "🇫🇷",
  "BRAZIL": "🇧🇷",
  "MEXICO": "🇲🇽",
  "CANADA": "🇨🇦",
  "AUSTRALIA": "🇦🇺",
  "SOUTH KOREA": "🇰🇷",
  "ITALY": "🇮🇹",
  "SPAIN": "🇪🇸",
  "TURKEY": "🇹🇷",
  "ISRAEL": "🇮🇱",
  "UAE": "🇦🇪",
  "UNITED ARAB EMIRATES": "🇦🇪",
  "SOUTH AFRICA": "🇿🇦",
  "EGYPT": "🇪🇬",
  "ARGENTINA": "🇦🇷",
  "COLOMBIA": "🇨🇴",
  "IRAN": "🇮🇷",
  "IRAQ": "🇮🇶",
  "UKRAINE": "🇺🇦",
  "POLAND": "🇵🇱",
  "NETHERLANDS": "🇳🇱",
  "SWITZERLAND": "🇨🇭",
  "SINGAPORE": "🇸🇬",
  "HONG KONG": "🇭🇰",
  "TAIWAN": "🇹🇼",
  "INDONESIA": "🇮🇩",
  "PHILIPPINES": "🇵🇭",
  "THAILAND": "🇹🇭",
  "VIETNAM": "🇻🇳",
  "MALAYSIA": "🇲🇾",
  "KENYA": "🇰🇪",
  "GHANA": "🇬🇭",
  "QATAR": "🇶🇦",
  "KUWAIT": "🇰🇼",
  "BAHRAIN": "🇧🇭",
  "LEBANON": "🇱🇧",
  "JORDAN": "🇯🇴",
  "AFGHANISTAN": "🇦🇫",
};

export function getCountryFlag(country: string | null | undefined): string | null {
  if (!country) return null;
  return COUNTRY_FLAGS[country.toUpperCase().trim()] || null;
}

/** US-only pipeline steps that are skipped for international subjects */
export const US_ONLY_STEPS = [
  "FEC",
  "SEC",
  "CourtListener",
  "Lobbying",
  "Bankruptcy",
  "USAspending",
  "SAM.gov",
  "Debarment",
];

/** Check if a step name matches a US-only step */
export function isUSOnlyStep(stepName: string): boolean {
  const lower = stepName.toLowerCase();
  return US_ONLY_STEPS.some(s => lower.includes(s.toLowerCase()));
}
