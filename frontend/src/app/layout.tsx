import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "PrimeLift AI",
  description: "ML-first causal decision dashboard for experimentation and growth.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
