import type { Metadata } from "next";
import { Inter, Manrope } from "next/font/google";
import "@/app/globals.css";

const inter = Inter({
  display: "swap",
  subsets: ["latin", "cyrillic"],
  variable: "--font-inter"
});

const manrope = Manrope({
  display: "swap",
  subsets: ["latin", "cyrillic"],
  variable: "--font-manrope",
  weight: ["400", "500", "600", "700", "800"]
});

export const metadata: Metadata = {
  title: "AI FitFabrica",
  description: "AI FitFabrica"
};

export default function RootLayout({
  children
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html className={`${inter.variable} ${manrope.variable}`} lang="ru">
      <body className="font-[family-name:var(--font-inter)]">{children}</body>
    </html>
  );
}
