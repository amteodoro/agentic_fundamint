"use client";

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface ProfileData {
  longName?: string;
  sector?: string;
  fullTimeEmployees?: number;
  longBusinessSummary?: string;
  country?: string;
  website?: string;
}

export function CompanyProfile({ ticker }: { ticker: string }) {
  const [profile, setProfile] = useState<ProfileData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (ticker) {
      const fetchProfile = async () => {
        try {
          setLoading(true);
          setError(null);
          const response = await fetch(`http://localhost:8000/api/stock/${ticker}/profile`);
          if (!response.ok) {
            throw new Error('Failed to fetch company profile.');
          }
          const data = await response.json();
          setProfile(data);
        } catch (err: any) {
          setError(err.message);
        } finally {
          setLoading(false);
        }
      };
      fetchProfile();
    }
  }, [ticker]);

  if (loading) return <p>Loading company profile...</p>;
  if (error) return <p className="text-red-500">{error}</p>;
  if (!profile) return <p>No profile data available.</p>;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Company Profile</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-lg font-semibold">{profile.longName}</p>
        <p className="text-sm text-gray-500">{profile.sector}</p>
        <p className="mt-4">{profile.longBusinessSummary}</p>
        <div className="mt-4 grid grid-cols-2 gap-4">
          <div>
            <p className="font-semibold">Country</p>
            <p>{profile.country}</p>
          </div>
          <div>
            <p className="font-semibold">Website</p>
            {profile.website && (
              <a href={profile.website} target="_blank" rel="noopener noreferrer" className="text-blue-500 hover:underline">
                {profile.website}
              </a>
            )}
          </div>
          <div>
            <p className="font-semibold">Full-Time Employees</p>
            <p>{profile.fullTimeEmployees?.toLocaleString()}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
