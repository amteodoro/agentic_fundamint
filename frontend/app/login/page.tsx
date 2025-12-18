"use client";

import { useAuth } from '@/app/context/AuthContext';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useState } from 'react';
import Link from 'next/link';

export default function LoginPage() {
    const { login, loginAsGuest, isLoading } = useAuth();
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setIsSubmitting(true);

        try {
            await login({ email, password });
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Login failed. Please try again.');
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleGuestLogin = () => {
        setIsSubmitting(true);
        setTimeout(() => {
            loginAsGuest();
            setIsSubmitting(false);
        }, 500);
    };

    return (
        <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4 py-12 sm:px-6 lg:px-8">
            <Card className="w-full max-w-md bg-white border-gray-200 shadow-lg">
                <CardHeader className="space-y-1">
                    <CardTitle className="text-2xl font-bold text-center text-gray-900">Sign in to Fundamint</CardTitle>
                    <CardDescription className="text-center text-gray-600">
                        Enter your email and password to access your portfolio
                    </CardDescription>
                </CardHeader>
                <form onSubmit={handleLogin}>
                    <CardContent className="grid gap-4">
                        {error && (
                            <div className="p-3 text-sm text-red-700 bg-red-50 rounded-lg border border-red-200">
                                {error}
                            </div>
                        )}
                        <div className="grid gap-2">
                            <Label htmlFor="email" className="text-gray-700">Email</Label>
                            <Input
                                id="email"
                                type="email"
                                placeholder="investor@example.com"
                                value={email}
                                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setEmail(e.target.value)}
                                required
                                className="bg-white border-gray-300 text-gray-900 placeholder:text-gray-400 focus:border-emerald-500 focus:ring-emerald-500"
                            />
                        </div>
                        <div className="grid gap-2">
                            <Label htmlFor="password" className="text-gray-700">Password</Label>
                            <Input
                                id="password"
                                type="password"
                                value={password}
                                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setPassword(e.target.value)}
                                required
                                className="bg-white border-gray-300 text-gray-900 placeholder:text-gray-400 focus:border-emerald-500 focus:ring-emerald-500"
                            />
                        </div>
                        <Button
                            type="submit"
                            disabled={isLoading || isSubmitting}
                            className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-semibold transition-all duration-200"
                        >
                            {isSubmitting ? "Signing in..." : "Sign In"}
                        </Button>
                        <div className="relative">
                            <div className="absolute inset-0 flex items-center">
                                <span className="w-full border-t border-gray-200" />
                            </div>
                            <div className="relative flex justify-center text-xs uppercase">
                                <span className="bg-white px-2 text-gray-500">
                                    Or continue with
                                </span>
                            </div>
                        </div>
                        <Button
                            type="button"
                            variant="outline"
                            onClick={handleGuestLogin}
                            disabled={isLoading || isSubmitting}
                            className="w-full border-gray-300 text-gray-700 hover:bg-gray-50 transition-all duration-200"
                        >
                            {isSubmitting ? "Signing in..." : "Guest Access (No Account Needed)"}
                        </Button>
                    </CardContent>
                </form>
                <CardFooter className="flex flex-col gap-3">
                    <div className="text-sm text-center text-gray-600">
                        Don&apos;t have an account?{' '}
                        <Link href="/register" className="text-emerald-600 hover:text-emerald-700 underline-offset-4 hover:underline transition-colors font-medium">
                            Create one
                        </Link>
                    </div>
                    <p className="text-xs text-center text-gray-500">
                        Guest access provides limited functionality. Create an account to save portfolios and watchlists.
                    </p>
                </CardFooter>
            </Card>
        </div>
    );
}
