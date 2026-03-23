import type { Metadata } from "next";
import { appName } from "@learnable/config";
import "./globals.css";

export const metadata: Metadata = {
  title: `${appName} | Local-First Research and Learning`,
  description: "Evidence-grounded deep research and study workflows powered by local AI."
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
