import type { Metadata } from "next";
import { JetBrains_Mono, Space_Grotesk } from "next/font/google";
import { TopBar } from "@/components/layout/TopBar";
import { DiagnosticProvider } from "@/context/DiagnosticContext";
import "./globals.css";

const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-space-grotesk",
});

const jetBrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-jetbrains-mono",
});

export const metadata: Metadata = {
  title: { default: "BolsaLAB", template: "%s · BolsaLAB" },
  description: "Descubre cómo reaccionarías si la bolsa cae, antes de que pase.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="es"
      className={`${spaceGrotesk.variable} ${jetBrainsMono.variable}`}
      suppressHydrationWarning
    >
      <body className="flex min-h-dvh flex-col">
        <TopBar />
        <DiagnosticProvider>{children}</DiagnosticProvider>
      </body>
    </html>
  );
}
