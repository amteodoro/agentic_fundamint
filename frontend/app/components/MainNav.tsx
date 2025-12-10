"use client";

import Link from "next/link";
import { useAuth } from "@/app/context/AuthContext";
import { Button } from "@/components/ui/button";

export function MainNav() {
  const { user, logout } = useAuth();

  return (
    <nav className="border-b bg-white p-4">
      <div className="container mx-auto flex items-center justify-between">
        <Link href="/" className="text-2xl font-bold text-blue-600">
          Fundamint
        </Link>
        <div className="flex items-center gap-4">
          <Link href="/" className="text-gray-600 hover:text-blue-600">
            Search
          </Link>
          {user ? (
            <>
              <span className="text-sm text-gray-600">
                Hi, {user.name} {user.isGuest && "(Guest)"}
              </span>
              <Button variant="ghost" onClick={logout}>
                Logout
              </Button>
            </>
          ) : (
            <Link href="/login">
              <Button variant="outline">Login</Button>
            </Link>
          )}
        </div>
      </div>
    </nav>
  );
}
