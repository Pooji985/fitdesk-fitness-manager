import React, { useEffect, useState } from 'react';
import { AlertTriangle, Mail, Phone, RefreshCw, Shield, UserRound, Users } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { memberService } from '../services/memberService';

const MEMBERSHIP_TIERS = ['Basic', 'Premium', 'Drop-in', 'Basic Tier', 'Premium Member', 'Unlimited All-Access', 'Drop-In Pass'];

function contactDraft(member) {
  return {
    phone: member.phone || '',
    emergency_contact_name: member.emergency_contact_name || '',
    emergency_contact_phone: member.emergency_contact_phone || '',
  };
}

export default function Members() {
  const { isAdmin, isAuthenticated, authLoading } = useAuth();
  const [members, setMembers] = useState([]);
  const [drafts, setDrafts] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [savingMemberId, setSavingMemberId] = useState(null);
  const [notice, setNotice] = useState('');

  const loadMembers = async () => {
    setLoading(true);
    setError('');
    try {
      const records = await memberService.getMembers();
      setMembers(records);
      setDrafts(Object.fromEntries(records.map((member) => [member.id, contactDraft(member)])));
    } catch (requestError) {
      setError(requestError.data?.detail || requestError.message || 'Could not load members.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (authLoading) return;
    if (isAuthenticated && isAdmin) loadMembers();
    else setLoading(false);
  }, [authLoading, isAuthenticated, isAdmin]);

  const updateMember = async (memberId, updates) => {
    setSavingMemberId(memberId);
    setError('');
    setNotice('');
    try {
      const updated = await memberService.updateMember(memberId, updates);
      setMembers((records) => records.map((member) => member.id === memberId ? updated : member));
      setDrafts((values) => ({ ...values, [memberId]: contactDraft(updated) }));
      setNotice(`Updated ${updated.name}.`);
    } catch (requestError) {
      setError(requestError.data?.detail || requestError.message || 'Could not update member.');
    } finally {
      setSavingMemberId(null);
    }
  };

  if (!authLoading && (!isAuthenticated || !isAdmin)) {
    return (
      <div className="p-8 text-center rounded-2xl glass-panel border border-slate-800 space-y-2">
        <Shield className="w-8 h-8 mx-auto text-amber-400" />
        <p className="text-sm font-semibold text-slate-200">Admin access required</p>
        <p className="text-xs text-slate-400">Member records are restricted to authenticated Administrators.</p>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white">Member Directory</h1>
          <p className="text-xs sm:text-sm text-slate-400">Member contact details, membership tiers, and active status.</p>
        </div>
        <span className="text-xs text-slate-400">{members.length} members</span>
      </div>

      {notice && <p role="status" className="text-xs text-emerald-300">{notice}</p>}
      {error && (
        <div role="alert" className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 flex items-center gap-2 text-xs">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
          <button type="button" onClick={loadMembers} title="Reload members" className="ml-auto"><RefreshCw className="w-3.5 h-3.5" /></button>
        </div>
      )}

      {loading ? (
        <div className="p-8 text-center text-xs text-slate-400"><RefreshCw className="inline w-4 h-4 mr-2 animate-spin" />Loading members...</div>
      ) : members.length === 0 ? (
        <div className="p-8 text-center rounded-2xl glass-panel border border-slate-800 space-y-2">
          <Users className="w-8 h-8 mx-auto text-slate-500" />
          <p className="text-sm font-semibold text-slate-200">No members found</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {members.map((member) => {
            const draft = drafts[member.id] || contactDraft(member);
            const saving = savingMemberId === member.id;
            const tierOptions = [...new Set([...MEMBERSHIP_TIERS, member.membership_tier].filter(Boolean))];
            return (
              <article key={member.id} className="p-4 sm:p-5 rounded-2xl glass-card border border-slate-800 space-y-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="w-10 h-10 rounded-xl bg-slate-800 flex items-center justify-center text-xs font-bold text-slate-200">
                      {member.avatar || member.name.split(/\s+/).map((part) => part[0]).slice(0, 2).join('').toUpperCase()}
                    </div>
                    <div className="min-w-0">
                      <h2 className="font-semibold text-sm text-white truncate">{member.name}</h2>
                      <p className="text-[11px] text-slate-400 truncate">{member.email}</p>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => updateMember(member.id, { is_active: !member.is_active })}
                    disabled={saving}
                    className={`shrink-0 px-2.5 py-1 rounded-full border text-[10px] font-semibold disabled:opacity-50 ${member.is_active ? 'text-emerald-300 bg-emerald-500/10 border-emerald-500/20' : 'text-rose-300 bg-rose-500/10 border-rose-500/20'}`}
                  >
                    {saving ? 'Saving...' : member.is_active ? 'Active · Deactivate' : 'Inactive · Activate'}
                  </button>
                </div>

                <label className="flex items-center justify-between gap-3 text-xs">
                  <span className="text-slate-400">Membership tier</span>
                  <select
                    value={member.membership_tier || ''}
                    onChange={(event) => updateMember(member.id, { membership_tier: event.target.value || null })}
                    disabled={saving}
                    className="max-w-[65%] px-2.5 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 text-xs"
                  >
                    <option value="">No tier set</option>
                    {tierOptions.map((tier) => <option key={tier} value={tier}>{tier}</option>)}
                  </select>
                </label>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-3 border-t border-slate-800/80">
                  <label className="space-y-1 text-[11px]">
                    <span className="flex items-center gap-1.5 text-slate-400"><Phone className="w-3 h-3" />Phone</span>
                    <input
                      value={draft.phone}
                      onChange={(event) => setDrafts((values) => ({ ...values, [member.id]: { ...draft, phone: event.target.value } }))}
                      className="w-full px-2.5 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-slate-200"
                    />
                  </label>
                  <label className="space-y-1 text-[11px]">
                    <span className="flex items-center gap-1.5 text-slate-400"><UserRound className="w-3 h-3" />Emergency contact</span>
                    <input
                      value={draft.emergency_contact_name}
                      onChange={(event) => setDrafts((values) => ({ ...values, [member.id]: { ...draft, emergency_contact_name: event.target.value } }))}
                      className="w-full px-2.5 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-slate-200"
                    />
                  </label>
                  <label className="space-y-1 text-[11px] sm:col-start-2">
                    <span className="flex items-center gap-1.5 text-slate-400"><Mail className="w-3 h-3" />Emergency phone</span>
                    <input
                      value={draft.emergency_contact_phone}
                      onChange={(event) => setDrafts((values) => ({ ...values, [member.id]: { ...draft, emergency_contact_phone: event.target.value } }))}
                      className="w-full px-2.5 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-slate-200"
                    />
                  </label>
                  <button
                    type="button"
                    onClick={() => updateMember(member.id, draft)}
                    disabled={saving}
                    className="sm:col-start-1 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold disabled:opacity-50"
                  >
                    {saving ? 'Saving...' : 'Save contact details'}
                  </button>
                </div>
              </article>
            );
          })}
        </div>
      )}
    </div>
  );
}
