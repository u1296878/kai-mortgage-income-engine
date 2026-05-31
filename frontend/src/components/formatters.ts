import type { BoundingBox } from "../types/api";

export function toCurrency(value: number | null): string {
  if (value == null) {
    return "n/a";
  }
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2,
  }).format(value);
}

export function toDate(value: string): string {
  return new Date(value).toLocaleString();
}

export function formatBoundingBox(box: BoundingBox): string {
  return `x1:${box.x1.toFixed(1)} y1:${box.y1.toFixed(1)} x2:${box.x2.toFixed(1)} y2:${box.y2.toFixed(1)}`;
}
