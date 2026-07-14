import { statusClass } from "@/utils/format";

export function Badge({ value }: { value?: string | boolean }) {
  const text = typeof value === "boolean" ? (value ? "active" : "inactive") : value || "normal";

  return <span className={`badge ${statusClass(text)}`}>{text}</span>;
}
