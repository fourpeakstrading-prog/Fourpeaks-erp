/** Format a decimal string as OMR with three decimals and thousands separators. */
export function omr(value: string | number, blankZero = false): string {
  const n = typeof value === "number" ? value : Number(value);
  if (Number.isNaN(n)) return "";
  if (blankZero && n === 0) return "";
  return n.toLocaleString("en-GB", { minimumFractionDigits: 3, maximumFractionDigits: 3 });
}

/** Parse what a person typed into a 3-decimal string, or null if it's not a number. */
export function parseAmount(text: string): string | null {
  const t = text.replace(/,/g, "").trim();
  if (t === "") return "0";
  if (!/^\d+(\.\d{0,3})?$/.test(t)) return null;
  return Number(t).toFixed(3);
}

export function monthName(m: number): string {
  return new Date(2000, m - 1, 1).toLocaleString("en-GB", { month: "long" });
}

export function today(): string {
  return new Date().toISOString().slice(0, 10);
}
