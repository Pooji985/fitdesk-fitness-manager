import React, { useEffect, useState } from 'react';
import { AlertTriangle, CheckCircle2, RefreshCw, Save, UserRound } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { memberService } from '../services/memberService';

export default function MyProfile() {
  const { user, isAuthenticated, isMember, authLoading } = useAuth();
  const [profile, setProfile] = useState(null);
  const [form, setForm] = useState({ phone: '', emergency_contact_name: '', emergency_contact_phone: '' });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const loadProfile = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await memberService.getMyProfile();
      setProfile(data);
      setForm({
        phone: data.phone || '',
        emergency_contact_name: data.emergency_contact_name || '',
        emergency_contact_phone: data.emergency_contact_phone || '',
      });
    } catch (requestError) {
      setError(requestError.data?.detail || requestError.message || 'Could not load your profile.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (authLoading) return;
    if (isAuthenticated && isMember) loadProfile();
    else setLoading(false);
  }, [authLoading, isAuthenticated, isMember, user.id]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setSaving(true);
    setError('');
    setNotice('');
    try {
      const updated = await memberService.updateMyProfile(form);
      setProfile(updated);
      setNotice('Profile saved.');
    } catch (requestError) {
      setError(requestError.data?.detail || requestError.message || 'Could not save your profile.');
    } finally {
      setSaving(false);
    }
  };

  if (!authLoading && (!isAuthenticated || !isMember)) {
    return (
      <div className="p-8 text-center rounded-2xl glass-panel border border-slate-800 space-y-2">
        <UserRound className="w-8 h-8 mx-auto text-slate-500" />
        <p className="text-sm font-semibold text-slate-200">Member sign-in required</p>
        <p className="text-xs text-slate-400">Sign in as a Member to view and update your contact profile.</p>
      </div>
    );
  }

  if (loading) {
    return <div className="p-8 text-center text-xs text-slate-400"><RefreshCw className="inline w-4 h-4 mr-2 animate-spin" />Loading profile...</div>;
  }

  return (
    <div className="max-w-2xl space-y-5">
      <div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-white">My Profile</h1>
        <p className="text-xs sm:text-sm text-slate-400">Update your contact and emergency contact details.</p>
      </div>
      {notice && <p role="status" className="inline-flex items-center gap-2 text-xs text-emerald-300"><CheckCircle2 className="w-4 h-4" />{notice}</p>}
      {error && (
        <div role="alert" className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 flex items-center gap-2 text-xs">
          <AlertTriangle className="w-4 h-4 shrink-0" /><span>{error}</span>
          <button type="button" onClick={loadProfile} className="ml-auto underline">Retry</button>
        </div>
      )}
      {profile && (
        <form onSubmit={handleSubmit} className="p-5 rounded-2xl glass-panel border border-slate-800 space-y-4">
          <div className="pb-3 border-b border-slate-800">
            <p className="text-sm font-semibold text-white">{profile.name}</p>
            <p className="text-xs text-slate-400">{profile.email}</p>
            <p className="mt-1 text-[11px] text-slate-500">{user.membershipTier || 'Membership tier'} · managed by your gym</p>
          </div>
          {[
            ['phone', 'Phone'],
            ['emergency_contact_name', 'Emergency contact name'],
            ['emergency_contact_phone', 'Emergency contact phone'],
          ].map(([key, label]) => (
            <label key={key} className="block space-y-1.5 text-xs">
              <span className="text-slate-300">{label}</span>
              <input
                value={form[key]}
                maxLength={key === 'emergency_contact_name' ? 100 : 30}
                onChange={(event) => setForm((values) => ({ ...values, [key]: event.target.value }))}
                className="w-full px-3 py-2.5 rounded-lg bg-slate-950 border border-slate-800 text-slate-100 focus:outline-none focus:border-emerald-500"
              />
            </label>
          ))}
          <button type="submit" disabled={saving} className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-emerald-500 text-slate-950 text-xs font-semibold disabled:opacity-50">
            <Save className="w-3.5 h-3.5" />{saving ? 'Saving...' : 'Save profile'}
          </button>
        </form>
      )}
    </div>
  );
}
