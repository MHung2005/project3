import type { Metadata } from "next";
import { Be_Vietnam_Pro, IBM_Plex_Mono, Newsreader } from "next/font/google";
import { Providers } from "@/components/providers";
import "./globals.css";

// Titles that name something: a course, a chapter, a page
const newsreader = Newsreader({
  subsets: ["latin", "vietnamese"],
  weight: ["500"],
  variable: "--font-newsreader",
  display: "swap",
});

// Everything else; drawn for Vietnamese diacritics
const beVietnam = Be_Vietnam_Pro({
  subsets: ["latin", "vietnamese"],
  weight: ["400", "500", "600"],
  variable: "--font-be-vietnam",
  display: "swap",
});

// Measured things: timecodes, percentages, scores
const plexMono = IBM_Plex_Mono({
  subsets: ["latin", "vietnamese"],
  weight: ["500"],
  variable: "--font-plex-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: { default: "Uniwise – Học trực tuyến", template: "%s – Uniwise" },
  description: "Nền tảng học trực tuyến: khóa học video, tài liệu, bài kiểm tra và theo dõi tiến độ học tập.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="vi" className={`${newsreader.variable} ${beVietnam.variable} ${plexMono.variable}`}>
      <body className="min-h-screen">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
