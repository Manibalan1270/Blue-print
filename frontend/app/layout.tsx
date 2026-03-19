import type { Metadata } from "next";
import Link from "next/link";
import type { ReactNode } from "react";
import "./globals.css";

export const metadata: Metadata = {
  title: "DevPulse AI",
  description: "Control room interface for engineering insights.",
};

const navItems = [
  { name: "Dashboard", href: "/" },
  { name: "Team Risks", href: "/team-risks" },
  { name: "Impact Logs", href: "/impact-logs" },
  { name: "Settings", href: "/settings" },
];

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-zinc-950 text-white antialiased">
        <div className="relative min-h-screen">
          <aside className="fixed inset-y-0 left-0 z-30 w-64 border-r border-zinc-800 bg-zinc-950">
            <div className="flex h-full flex-col p-6">
              <div className="mb-8">
                <p className="text-xs uppercase tracking-[0.2em] text-zinc-400">DevPulse AI</p>
                <h1 className="mt-2 text-xl font-semibold">Control Room</h1>
              </div>

              <nav className="space-y-1">
                {navItems.map((item) => (
                  <Link
                    key={item.name}
                    href={item.href}
                    className="block rounded-md px-3 py-2 text-sm text-zinc-200 transition hover:bg-zinc-800 hover:text-white"
                  >
                    {item.name}
                  </Link>
                ))}
              </nav>
            </div>
          </aside>

          <main className="ml-0 min-h-screen md:ml-64">
            <div className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8">{children}</div>
          </main>
        </div>
      </body>
    </html>
  );
}
