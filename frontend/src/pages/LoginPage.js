import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Separator } from '../components/ui/separator';
import { toast } from 'sonner';
import { LogIn, UserPlus, Globe, Shield } from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export default function LoginPage({ onAuth }) {
  const [loginEmail, setLoginEmail] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [regName, setRegName] = useState('');
  const [regEmail, setRegEmail] = useState('');
  const [regPassword, setRegPassword] = useState('');
  const [loading, setLoading] = useState(false);

  // REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
  const handleGoogleLogin = () => {
    const redirectUrl = window.location.origin + '/';
    window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const r = await fetch(`${API_URL}/api/auth/login`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ email: loginEmail, password: loginPassword }),
      });
      if (!r.ok) { const err = await r.json(); throw new Error(err.detail || 'Login failed'); }
      const data = await r.json();
      localStorage.setItem('session_token', data.session_token);
      onAuth(data);
      toast.success('Welcome back!');
    } catch (e) { toast.error(e.message); }
    finally { setLoading(false); }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const r = await fetch(`${API_URL}/api/auth/register`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ email: regEmail, password: regPassword, name: regName }),
      });
      if (!r.ok) { const err = await r.json(); throw new Error(err.detail || 'Registration failed'); }
      const data = await r.json();
      localStorage.setItem('session_token', data.session_token);
      onAuth(data);
      toast.success('Account created!');
    } catch (e) { toast.error(e.message); }
    finally { setLoading(false); }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4" style={{ background: 'linear-gradient(135deg, #0f2137 0%, #1a3a5c 50%, #0f2137 100%)' }} data-testid="login-page">
      <Card className="w-full max-w-md border-0 shadow-2xl">
        <CardHeader className="text-center pb-2">
          <div className="flex items-center justify-center gap-3 mb-3">
            <img src="/a2-intelligence-logo.png" alt="A2 Intelligence" className="h-14 w-14 rounded-lg object-contain" />
          </div>
          <CardTitle className="text-xl" style={{ color: '#0f2137' }}>A2 Intelligence</CardTitle>
          <p className="text-xs text-muted-foreground">Climate Risk Analytics by AA Impact Inc.</p>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Google Auth */}
          <Button variant="outline" className="w-full h-11" onClick={handleGoogleLogin} data-testid="google-login-btn">
            <Globe className="h-4 w-4 mr-2" />
            Continue with Google
          </Button>

          <div className="relative">
            <Separator />
            <span className="absolute left-1/2 -translate-x-1/2 -translate-y-1/2 bg-card px-2 text-xs text-muted-foreground">
              or use email
            </span>
          </div>

          <Tabs defaultValue="login">
            <TabsList className="w-full">
              <TabsTrigger value="login" className="flex-1" data-testid="tab-login">
                <LogIn className="h-3 w-3 mr-1" />Login
              </TabsTrigger>
              <TabsTrigger value="register" className="flex-1" data-testid="tab-register">
                <UserPlus className="h-3 w-3 mr-1" />Register
              </TabsTrigger>
            </TabsList>

            <TabsContent value="login">
              <form onSubmit={handleLogin} className="space-y-3 mt-3">
                <div>
                  <Label htmlFor="login-email" className="text-xs">Email</Label>
                  <Input id="login-email" type="email" value={loginEmail} onChange={e => setLoginEmail(e.target.value)}
                    placeholder="you@example.com" required data-testid="login-email" />
                </div>
                <div>
                  <Label htmlFor="login-password" className="text-xs">Password</Label>
                  <Input id="login-password" type="password" value={loginPassword} onChange={e => setLoginPassword(e.target.value)}
                    placeholder="••••••••" required data-testid="login-password" />
                </div>
                <Button type="submit" className="w-full" disabled={loading} data-testid="login-submit">
                  {loading ? 'Signing in...' : 'Sign In'}
                </Button>
              </form>
            </TabsContent>

            <TabsContent value="register">
              <form onSubmit={handleRegister} className="space-y-3 mt-3">
                <div>
                  <Label htmlFor="reg-name" className="text-xs">Name</Label>
                  <Input id="reg-name" value={regName} onChange={e => setRegName(e.target.value)}
                    placeholder="Your name" required data-testid="register-name" />
                </div>
                <div>
                  <Label htmlFor="reg-email" className="text-xs">Email</Label>
                  <Input id="reg-email" type="email" value={regEmail} onChange={e => setRegEmail(e.target.value)}
                    placeholder="you@example.com" required data-testid="register-email" />
                </div>
                <div>
                  <Label htmlFor="reg-password" className="text-xs">Password</Label>
                  <Input id="reg-password" type="password" value={regPassword} onChange={e => setRegPassword(e.target.value)}
                    placeholder="Min 6 characters" required minLength={6} data-testid="register-password" />
                </div>
                <Button type="submit" className="w-full" disabled={loading} data-testid="register-submit">
                  {loading ? 'Creating account...' : 'Create Account'}
                </Button>
              </form>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}
