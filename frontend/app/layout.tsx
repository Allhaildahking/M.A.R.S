import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = { title: "M.A.R.S. | Personal Intelligence System", description: "A private workspace for thinking, research, and building." };

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
