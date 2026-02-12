// app/layout.tsx  or  src/app/layout.tsx
import './globals.css';           // ← same folder
// or   import '@/app/globals.css';   if you have path alias @ → src

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru" suppressHydrationWarning>  {/* good for dark mode later */}
      <body>{children}</body>
    </html>
  );
}
