"use client";

import { useAuth } from '@/app/context/AuthContext';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useState } from 'react';

export default function LoginPage() {
    const { loginAsGuest } = useAuth();
    const [isLoading, setIsLoading] = useState(false);

    const handleGuestLogin = () => {
        setIsLoading(true);
        // Simulate a small delay for effect
        setTimeout(() => {
            loginAsGuest();
            setIsLoading(false);
        }, 500);
    };

    return (
        <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4 py-12 sm:px-6 lg:px-8">
            <Card className="w-full max-w-md">
                <CardHeader className="space-y-1">
                    <CardTitle className="text-2xl font-bold text-center">Sign in to Fundamint</CardTitle>
                    <CardDescription className="text-center">
                        Enter your email and password to access your portfolio
                    </CardDescription>
                </CardHeader>
                <CardContent className="grid gap-4">
                    <div className="grid gap-2">
                        <Label htmlFor="email">Email</Label>
                        <Input id="email" type="email" placeholder="m@example.com" disabled />
                    </div>
                    <div className="grid gap-2">
                        <Label htmlFor="password">Password</Label>
                        <Input id="password" type="password" disabled />
                    </div>
                    <div className="relative">
                        <div className="absolute inset-0 flex items-center">
                            <span className="w-full border-t" />
                        </div>
                        <div className="relative flex justify-center text-xs uppercase">
                            <span className="bg-white px-2 text-muted-foreground">
                                Or continue with
                            </span>
                        </div>
                    </div>
                    <Button variant="outline" onClick={handleGuestLogin} disabled={isLoading} className="w-full">
                        {isLoading ? "Signing in..." : "Guest Access (Testing)"}
                    </Button>
                </CardContent>
                <CardFooter className="flex flex-col gap-2">
                    <p className="text-xs text-center text-gray-500">
                        Note: Standard authentication is currently disabled. Use Guest Access to test features.
                    </p>
                </CardFooter>
            </Card>
        </div>
    );
}
