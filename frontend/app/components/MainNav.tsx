"use client";

import Link from "next/link";
import { useAuth } from "@/app/context/AuthContext";
import { Button } from "@/components/ui/button";

export function MainNav() {
  const { user, logout, isAuthenticated } = useAuth();

  return (
    <nav className="border-b border-gray-200 bg-white shadow-sm p-4">
      <div className="container mx-auto flex items-center justify-between">
        <Link href="/" className="text-2xl font-bold text-emerald-600 hover:text-emerald-700 transition-colors">
          Fundamint
        </Link>
        <div className="flex items-center gap-4">
          <Link href="/" className="text-gray-600 hover:text-gray-900 transition-colors font-medium">
            Search
          </Link>
          {isAuthenticated && (
            <Link href="/portfolios" className="text-gray-600 hover:text-gray-900 transition-colors font-medium">
              Portfolios
            </Link>
          )}
          {user ? (
            <>
              <span className="text-sm text-gray-500">
                {user.name || user.email?.split('@')[0]} {user.is_guest && "(Guest)"}
              </span>
              <Button
                variant="ghost"
                onClick={logout}
                className="text-gray-600 hover:text-gray-900 hover:bg-gray-100"
              >
                Logout
              </Button>
            </>
          ) : (
            <Link href="/login">
              <Button variant="outline" className="border-emerald-500 text-emerald-600 hover:bg-emerald-50">
                Login
              </Button>
            </Link>
          )}
        </div>
      </div>
    </nav>
  );
}
