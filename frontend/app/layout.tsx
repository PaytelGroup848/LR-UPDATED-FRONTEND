import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "LR Remote Access Admin",
  description: "Admin frontend for LR Remote Access"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
