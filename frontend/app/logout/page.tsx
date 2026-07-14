"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { logout } from "@/services/auth.service";

export default function LogoutPage() {
  const router = useRouter();

  useEffect(() => {
    let active = true;

    async function signOut() {
      try {
        await logout();
      } catch {
        // Already logged out or backend unavailable; the user should still leave the portal.
      } finally {
        if (active) router.replace("/login");
      }
    }

    signOut();

    return () => {
      active = false;
    };
  }, [router]);

  return (
    <main className="auth-shell">
      <section className="auth-form-panel">
        <div className="auth-title">Signing out</div>
        <div className="auth-sub">Please wait...</div>
      </section>
    </main>
  );
}
