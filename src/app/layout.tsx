import type { Metadata, Viewport } from "next";
import { Instrument_Serif, Inter_Tight } from "next/font/google";
import "./globals.css";
import { asset } from "@/config/site";

const sans = Inter_Tight({ subsets: ["latin"], variable: "--font-inter-tight", display: "swap" });
const display = Instrument_Serif({
  subsets: ["latin"],
  weight: "400",
  style: ["normal", "italic"],
  variable: "--font-instrument-serif",
  display: "swap",
});

export const metadata: Metadata = {
  title: "ORDEN — Furniture & Objects",
  description: "Designed to belong. Three rooms, three pieces: step inside the ORDEN showroom and explore each piece in 3D, in four finishes.",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#F4F0E8",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${sans.variable} ${display.variable}`}>
      <head>
        {/* first room's still: the largest paint; the right one for the screen shape */}
        <link rel="preload" as="image" href={asset("/rooms/living/room-beauty.webp")} media="(min-aspect-ratio: 4/5)" fetchPriority="high" crossOrigin="anonymous" />
        <link rel="preload" as="image" href={asset("/rooms/living/room-p-beauty.webp")} media="(max-aspect-ratio: 4/5)" fetchPriority="high" crossOrigin="anonymous" />
      </head>
      <body className="font-sans">{children}</body>
    </html>
  );
}
