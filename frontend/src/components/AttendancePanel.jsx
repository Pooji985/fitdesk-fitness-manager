import React, { useEffect, useState } from 'react';
import { AlertTriangle, Check, ClipboardCheck, RefreshCw, UserRound, X } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { classService } from '../services/classService';
import { attendanceService } from '../services/attendanceService';

const STATUS_STYLES = {
  booked: 'text-cyan-300 bg-cyan-500/10 border-cyan-500/20',
  attended: 'text-emerald-300 bg-emerald-500/10 border-emerald-500/20',
  no_show: 'text-rose-300 bg-rose-500/10 border-rose-500/20',
};

export default function AttendancePanel() {
  const { user, isAdmin, isTrainer, isAuthenticated, authLoading } = useAuth();
  const [classes, setClasses] = useState([]);
  const [selectedClassId, setSelectedClassId] = useState('');
  const [roster, setRoster] = useState([]);
  const [loadingClasses, setLoadingClasses] = useState(true);
  const [loadingRoster, setLoadingRoster] = useState(false);
  const [updatingBookingId, setUpdatingBookingId] = useState(null);
  const [error, setError] = useState('');

  const loadClasses = async () => {
    setLoadingClasses(true);
    setError('');
    try {
      const assignedClasses = await classService.getClasses({
        trainer_id: isTrainer ? user.id : undefined,
        include_weather: false,
      });
      setClasses(assignedClasses);
      setSelectedClassId((currentId) => currentId && assignedClasses.some((item) => String(item.id) === currentId)
        ? currentId
        : assignedClasses.length ? String(assignedClasses[0].id) : '');
    } catch (requestError) {
      setError(requestError.data?.detail || requestError.message || 'Could not load classes.');
    } finally {
      setLoadingClasses(false);
    }
  };

  useEffect(() => {
    if (authLoading) return;
    if (isAuthenticated && (isAdmin || isTrainer)) loadClasses();
    else setLoadingClasses(false);
  }, [authLoading, isAuthenticated, isAdmin, isTrainer, user.id]);

  useEffect(() => {
    let isMounted = true;
    if (!selectedClassId) {
      setRoster([]);
      return () => { isMounted = false; };
    }

    setLoadingRoster(true);
    setError('');
    attendanceService.getClassAttendance(selectedClassId)
      .then((records) => { if (isMounted) setRoster(records); })
      .catch((requestError) => {
        if (isMounted) setError(requestError.data?.detail || requestError.message || 'Could not load attendance.');
      })
      .finally(() => { if (isMounted) setLoadingRoster(false); });

    return () => { isMounted = false; };
  }, [selectedClassId]);

  const markAttendance = async (bookingId, nextStatus) => {
    setUpdatingBookingId(bookingId);
    setError('');
    try {
      const updated = await attendanceService.updateBookingAttendance(bookingId, nextStatus);
      setRoster((records) => records.map((record) => record.booking_id === bookingId ? updated : record));
    } catch (requestError) {
      setError(requestError.data?.detail || requestError.message || 'Could not update attendance.');
    } finally {
      setUpdatingBookingId(null);
    }
  };

  if (authLoading || loadingClasses) {
    return <div className="p-8 text-center text-xs text-slate-400"><RefreshCw className="inline w-4 h-4 mr-2 animate-spin" />Loading attendance tools...</div>;
  }

  if (!isAuthenticated || (!isAdmin && !isTrainer)) {
    return (
      <div className="p-8 text-center rounded-2xl glass-panel border border-slate-800 space-y-2">
        <ClipboardCheck className="w-8 h-8 mx-auto text-slate-500" />
        <p className="text-sm font-semibold text-slate-200">Staff sign-in required</p>
        <p className="text-xs text-slate-400">Attendance is available to authenticated Admins and Trainers.</p>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-3">
        <label className="space-y-1.5 text-xs">
          <span className="block text-slate-400">Class session</span>
          <select
            value={selectedClassId}
            onChange={(event) => setSelectedClassId(event.target.value)}
            className="min-w-64 max-w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200"
            disabled={!classes.length}
          >
            {classes.length ? classes.map((fitnessClass) => (
              <option key={fitnessClass.id} value={fitnessClass.id}>
                {fitnessClass.title} · {new Date(fitnessClass.start_time).toLocaleString()}
              </option>
            )) : <option value="">No assigned classes</option>}
          </select>
        </label>
        <p className="text-[11px] text-slate-500">{classes.length} {isTrainer ? 'assigned ' : ''}classes</p>
      </div>

      {error && (
        <div role="alert" className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
          <button type="button" onClick={loadClasses} title="Reload classes" className="ml-auto"><RefreshCw className="w-3.5 h-3.5" /></button>
          <button type="button" onClick={() => setError('')} aria-label="Dismiss error"><X className="w-3.5 h-3.5" /></button>
        </div>
      )}

      {loadingRoster ? (
        <div className="p-8 text-center text-xs text-slate-400"><RefreshCw className="inline w-4 h-4 mr-2 animate-spin" />Loading enrolled members...</div>
      ) : !selectedClassId ? (
        <div className="p-8 text-center rounded-2xl glass-panel border border-slate-800 text-xs text-slate-400">No classes available for attendance.</div>
      ) : roster.length === 0 ? (
        <div className="p-8 text-center rounded-2xl glass-panel border border-slate-800 space-y-2">
          <UserRound className="w-7 h-7 mx-auto text-slate-500" />
          <p className="text-sm font-semibold text-slate-200">No enrolled members</p>
          <p className="text-xs text-slate-400">This class has no active bookings to mark.</p>
        </div>
      ) : (
        <div className="rounded-2xl glass-panel border border-slate-800 divide-y divide-slate-800/70">
          {roster.map((record) => (
            <div key={record.booking_id} className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-lg bg-slate-800 flex items-center justify-center text-xs font-bold text-slate-200">
                  {record.member_name.split(/\s+/).map((part) => part[0]).slice(0, 2).join('').toUpperCase()}
                </div>
                <div>
                  <p className="text-sm font-semibold text-slate-100">{record.member_name}</p>
                  <p className="text-[11px] text-slate-400">{new Date(record.start_time).toLocaleString()}</p>
                </div>
                <span className={`ml-2 px-2 py-0.5 rounded-full border text-[10px] font-semibold capitalize ${STATUS_STYLES[record.status] || STATUS_STYLES.booked}`}>
                  {record.status.replace('_', ' ')}
                </span>
              </div>
              <div className="flex flex-wrap gap-2 sm:justify-end">
                {['attended', 'no_show'].map((status) => (
                  <button
                    key={status}
                    type="button"
                    onClick={() => markAttendance(record.booking_id, status)}
                    disabled={record.status === status || updatingBookingId === record.booking_id}
                    className={`inline-flex items-center gap-1 px-2.5 py-1.5 rounded-md border text-[11px] font-medium capitalize disabled:opacity-40 ${status === 'attended' ? 'border-emerald-500/30 text-emerald-300 hover:bg-emerald-500/10' : 'border-rose-500/30 text-rose-300 hover:bg-rose-500/10'}`}
                  >
                    {record.status === status && <Check className="w-3 h-3" />}
                    {updatingBookingId === record.booking_id ? 'Saving...' : status.replace('_', ' ')}
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}