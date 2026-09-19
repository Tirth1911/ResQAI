'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/context/AuthContext';
import { UserRole } from '@/types';
import {
  ShieldAlert,
  Shield,
  Lock,
  Mail,
  ArrowRight,
  Sparkles,
  Radio,
  Truck,
  Building2,
  Eye,
  KeyRound,
  CheckCircle2,
  AlertCircle,
  Loader2
} from 'lucide-react';

const DEMO_ROLES: Array<{
  role: UserRole;
  title: string;
  email: string;
  department: string;
  icon: any;
  color: string;
  description: string;
}> = [
  {
    role: 'ADMIN',
    title: 'System Administrator',
    email: 'admin@resqai.org',
    department: 'Command Executive HQ',
    icon: ShieldAlert,
    color: 'text-red-700 bg-red-50 border-red-200',
    description: 'Full administrative access, infrastructure settings, crisis simulator, and database telemetry.',
  },
  {
    role: 'DISPATCHER',
    title: 'Emergency Dispatcher',
    email: 'dispatcher@resqai.org',
    department: 'Central 911 Operations',
    icon: Radio,
    color: 'text-blue-700 bg-blue-50 border-blue-200',
    description: 'AI incident triage, 3-Signal duplicate merging, multi-unit recommendations & fleet dispatch.',
  },
  {
    role: 'FIELD_TEAM',
    title: 'Field Response Lead',
    email: 'field@resqai.org',
    department: 'Rapid Response Unit 01',
    icon: Truck,
    color: 'text-emerald-700 bg-emerald-50 border-emerald-200',
    description: 'On-scene status updates (EN_ROUTE, IN_PROGRESS), live GPS telemetry, and casualty triage.',
  },
  {
    role: 'HOSPITAL',
    title: 'Trauma ER Coordinator',
    email: 'hospital@resqai.org',
    department: 'Level-1 Emergency ER',
    icon: Building2,
    color: 'text-purple-700 bg-purple-50 border-purple-200',
    description: 'Inbound ambulance tracking, critical ICU/Trauma bed occupancy, and mass casualty intake.',
  },
  {
    role: 'VIEWER',
    title: 'Public Observer',
    email: 'viewer@resqai.org',
    department: 'Public Safety Compliance',
    icon: Eye,
    color: 'text-slate-700 bg-slate-100 border-slate-200',
    description: 'Read-only cartography observation, live incident feeds, and executive SLA analytics.',
  },
];

export default function LoginPage() {
  const router = useRouter();
  const { login, quickLogin, isLoading, user } = useAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [activeQuickRole, setActiveQuickRole] = useState<UserRole | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage('');
    setIsSubmitting(true);
    try {
      await login(email, password);
      router.push('/dashboard');
    } catch (err: any) {
      setErrorMessage(err.message || 'Authentication failed. Please check your credentials.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleQuickLogin = async (role: UserRole) => {
    setErrorMessage('');
    setActiveQuickRole(role);
    try {
      await quickLogin(role);
      router.push('/dashboard');
    } catch (err: any) {
      setErrorMessage(err.message || `Failed to login as ${role}`);
    } finally {
      setActiveQuickRole(null);
    }
  };

  return (
    <div className="min-h-screen w-full bg-slate-50 flex flex-col justify-between font-sans text-slate-900 p-4 md:p-8 selection:bg-red-500 selection:text-white">
      {/* Top Brand Header */}
      <div className="flex items-center justify-between border-b border-slate-200 pb-4 max-w-6xl mx-auto w-full">
        <Link href="/dashboard" className="flex items-center gap-2.5 group">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-red-600 text-white shadow-2xs">
            <Shield className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-base font-black tracking-tight text-slate-900">
              ResQ<span className="text-red-600">AI</span>
            </h1>
            <p className="text-[11px] text-slate-500 font-medium">
              Emergency Intelligence Platform
            </p>
          </div>
        </Link>

        <div className="flex items-center gap-2 text-xs">
          <Link
            href="/demo"
            className="flex items-center gap-1.5 rounded-md border border-emerald-200 bg-emerald-50 px-3 py-1.5 text-xs font-bold text-emerald-700 hover:bg-emerald-100 transition-colors shadow-2xs"
          >
            <Sparkles className="h-3.5 w-3.5 text-emerald-600" />
            <span>Interactive Demo Mode</span>
          </Link>
        </div>
      </div>

      {/* Main Login Body */}
      <div className="max-w-6xl mx-auto w-full my-6 grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column: 1-Click Role Switcher */}
        <div className="lg:col-span-7 space-y-4">
          <div>
            <span className="text-[10px] font-bold text-red-600 bg-red-50 px-2 py-0.5 rounded border border-red-200 uppercase tracking-wider">
              1-Click Role Access
            </span>
            <h2 className="text-xl font-extrabold text-slate-900 tracking-tight mt-2">
              Select Operator Command Role
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Click any pre-configured role below to log in instantly with live JWT credentials
            </p>
          </div>

          <div className="space-y-3">
            {DEMO_ROLES.map((r) => {
              const Icon = r.icon;
              const isPending = activeQuickRole === r.role;
              return (
                <div
                  key={r.role}
                  onClick={() => !isPending && handleQuickLogin(r.role)}
                  className={`group cursor-pointer rounded-lg border p-4 bg-white shadow-2xs hover:border-red-300 hover:shadow-xs transition-all flex items-start justify-between gap-4`}
                >
                  <div className="flex items-start gap-3">
                    <div className={`p-2.5 rounded-md border ${r.color}`}>
                      <Icon className="h-5 w-5" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="text-sm font-bold text-slate-900 group-hover:text-red-700 transition-colors">
                          {r.title}
                        </h3>
                        <span className="text-[10px] font-mono text-slate-400">({r.department})</span>
                      </div>
                      <p className="text-xs text-slate-500 mt-1 leading-relaxed">
                        {r.description}
                      </p>
                    </div>
                  </div>

                  <button
                    type="button"
                    disabled={isPending}
                    className="flex items-center gap-1 rounded bg-slate-900 hover:bg-red-600 text-white px-3 py-1.5 text-xs font-bold transition-colors shrink-0 shadow-2xs group-hover:bg-red-600"
                  >
                    {isPending ? (
                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    ) : (
                      <ArrowRight className="h-3.5 w-3.5" />
                    )}
                    <span>Sign In</span>
                  </button>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Column: Standard Email / Password Form */}
        <div className="lg:col-span-5 rounded-lg border border-slate-200 bg-white p-6 shadow-xs space-y-4">
          <div>
            <h3 className="text-base font-bold text-slate-900">Sign In with Credentials</h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Enter your authorized dispatch center email and password
            </p>
          </div>

          {errorMessage && (
            <div className="rounded-md bg-red-50 p-3 text-xs text-red-700 border border-red-200 flex items-start gap-2">
              <AlertCircle className="h-4 w-4 shrink-0 mt-0.5 text-red-600" />
              <span>{errorMessage}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4 text-xs">
            <div>
              <label className="block text-[11px] font-bold uppercase text-slate-600 mb-1">
                Command Email Address
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                <input
                  type="email"
                  required
                  placeholder="dispatcher@resqai.org"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full rounded-md border border-slate-200 bg-slate-50 pl-9 pr-3 py-2 text-xs text-slate-900 placeholder-slate-400 focus:border-red-500 focus:bg-white focus:outline-none"
                />
              </div>
            </div>

            <div>
              <label className="block text-[11px] font-bold uppercase text-slate-600 mb-1">
                Operator Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                <input
                  type="password"
                  required
                  placeholder="••••••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full rounded-md border border-slate-200 bg-slate-50 pl-9 pr-3 py-2 text-xs text-slate-900 placeholder-slate-400 focus:border-red-500 focus:bg-white focus:outline-none"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full flex items-center justify-center gap-2 rounded-md bg-red-600 hover:bg-red-700 py-2.5 text-xs font-bold text-white shadow-xs transition-colors disabled:opacity-50"
            >
              {isSubmitting ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <KeyRound className="h-4 w-4" />
              )}
              <span>Sign In with JWT</span>
            </button>
          </form>

          <div className="pt-3 border-t border-slate-100 text-[11px] text-slate-500 text-center">
            ResQAI Enterprise Emergency Response Platform • v0.1.0
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="border-t border-slate-200 pt-3 text-center text-[11px] text-slate-500 max-w-6xl mx-auto w-full">
        Real-time MongoDB Engine &bull; Geospatial 2dsphere indexing &bull; Leaflet GIS Cartography
      </div>
    </div>
  );
}
