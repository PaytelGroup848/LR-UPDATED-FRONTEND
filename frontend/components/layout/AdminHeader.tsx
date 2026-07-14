"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { buildApiUrl } from "@/services/api";
import { navItems } from "@/store/navigation";

export function AdminHeader() {
  const pathname = usePathname();

  return (
    <header className="topbar">
      <Link className="brand" href="/users">
        <span className="mark">
          <img alt="LR Remote Access" src="/lr-remote-logo.png" />
        </span>
        <span>LR Remote Access</span>
      </Link>
      <nav className="nav">
        {navItems.map((item) => (
          <Link
            className={`btn ${pathname === item.href ? "primary" : ""}`}
            href={item.href}
            key={item.href}
          >
            {item.label}
          </Link>
        ))}
        <a className="btn" href="/portal/">
          User Portal
        </a>
        <a className="btn green" download href={buildApiUrl("/api/download-admin-panel")}>
          Download Admin Panel
        </a>
        <a className="btn" href="/logout">
          Logout
        </a>
      </nav>
    </header>
  );
}
