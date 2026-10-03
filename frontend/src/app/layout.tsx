import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "As Snow Cleaning & Pest Control | Lagos",
  description:
    "5-star rated home cleaning, office cleaning, pest control and fumigation in Lagos. Get an instant quote and book on WhatsApp.",
  icons: { icon: "/favicon.svg" },
};
export const viewport: Viewport = { width: "device-width", initialScale: 1, themeColor: "#1b6fb5" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en-NG">
      <body>{children}</body>
    </html>
  );
}
