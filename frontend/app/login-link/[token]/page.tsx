"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/services/api";

export default function LoginLinkPage({ params }: { params: { token: string } }) {
  const router = useRouter();
  const [message, setMessage] = useState("Opening your portal...");

  useEffect(() => {
    let active = true;

    async function consumeLink() {
      try {
        await apiFetch(`/login-link/${encodeURIComponent(params.token)}?format=json`, {
          headers: { Accept: "application/json" }
        });
        if (active) router.replace("/portal");
      } catch (error) {
        if (active) {
          setMessage(error instanceof Error ? error.message : "Login link is invalid or expired.");
        }
      }
    }

    consumeLink();

    return () => {
      active = false;
    };
  }, [params.token, router]);

  return (
    <main className="auth-shell">
      <section className="auth-form-panel">
        <div className="auth-title">Login link</div>
        <div className="auth-sub">{message}</div>
      </section>
    </main>
  );
}
