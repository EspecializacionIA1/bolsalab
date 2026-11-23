import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "BolsaLAB",
  description: "Descubre cómo reaccionarías si la bolsa cae, antes de que pase.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}
