import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { AlertTriangle, BookmarkCheck, Calendar, Clock, MapPin, RefreshCw, UserRound, XCircle } from 'lucide-react';
import { bookingService } from '../services/bookingService';
import AttendancePanel from '../components/AttendancePanel';

const STATUS_STYLES = {
  booked: 'text-cyan-300 bg-cyan-500/10 border-cyan-500/20',
  attended: 'text-emerald-300 bg-emerald-500/10 border-emerald-500/20',
  cancelled: 'text-slate-300 bg-slate-500/10 border-slate-500/20',
  no_show: 'text-rose-300 bg-rose-500/10 border-rose-500/20',
};

function formatDate(value) {
  return new Date(value).toLocaleString('en-US', {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  });
}

export default function Bookings({ onNavigate }) {
  const { user, isMember, isAdmin, isTrainer, isAuthenticated, authLoading } = useAuth();
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [cancelingId, setCancelingId] = useState(null);
  const [notice, setNotice] = useState('');

  if (isAdmin || isTrainer) {
    return (
      <div className="space-y-5">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white">Attendance</h1>
          <p className="text-xs sm:text-sm text-slate-400">Review enrolled members and record their class attendance.</p>
        </div>
        <AttendancePanel />
      </div>
    );
  }

  const loadBookings = async () => {
    setLoading(true);
    setError('');
    try {
      setBookings(await bookingService.getMyBookings());
    } catch (requestError) {
      setError(requestError.data?.detail || requestError.message || 'Could not load bookings.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (authLoading) return;
    if (isAuthenticated) {
      loadBookings();
    } else {
      setBookings([]);
      setLoading(false);
    }
  }, [authLoading, isAuthenticated, user.id]);

  const handleCancel = async (bookingId) => {
    setCancelingId(bookingId);
    setError('');
    setNotice('');
    try {
      await bookingService.cancelBooking(bookingId);
      setNotice('Booking cancelled.');
      await loadBookings();
    } catch (requestError) {
      setError(requestError.data?.detail || requestError.message || 'Could not cancel booking.');
    } finally {
      setCancelingId(null);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white">
            {isAuthenticated ? 'My Class Bookings' : 'Class Bookings'}
          </h1>
          <p className="text-xs sm:text-sm text-slate-400">
            {isAuthenticated
              ? `Bookings for ${user.name}`
              : 'Sign in as a member to view and manage your reservations.'}
          </p>
        </div>
      </div>

      {notice && <p role="status" className="text-xs text-emerald-300">{notice}</p>}
      {error && (
        <div role="alert" className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 flex items-start gap-2 text-xs">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
          <button type="button" onClick={loadBookings} className="ml-auto underline">Retry</button>
        </div>
      )}

      {!isAuthenticated ? (
        <div className="p-8 text-center rounded-2xl glass-panel border border-slate-800 space-y-2">
          <BookmarkCheck className="w-8 h-8 mx-auto text-slate-500" />
          <p className="text-sm font-semibold text-slate-200">Sign in required</p>
          <p className="text-xs text-slate-400">Demo role switching does not grant access to personal bookings.</p>
        </div>
      ) : loading ? (
        <div className="p-8 text-center text-xs text-slate-400"><RefreshCw className="inline w-4 h-4 mr-2 animate-spin" />Loading bookings...</div>
      ) : error && bookings.length === 0 ? (
        <div className="p-8 text-center rounded-2xl glass-panel border border-slate-800 space-y-2">
          <AlertTriangle className="w-8 h-8 mx-auto text-rose-400" />
          <p className="text-sm font-semibold text-slate-200">Bookings unavailable</p>
          <p className="text-xs text-slate-400">Retry the request to check your latest reservations.</p>
        </div>
      ) : bookings.length === 0 ? (
        <div className="p-8 text-center rounded-2xl glass-panel border border-slate-800 space-y-3">
          <BookmarkCheck className="w-8 h-8 mx-auto text-slate-500" />
          <p className="text-sm font-semibold text-slate-200">No bookings yet</p>
          {isMember && onNavigate && (
            <button type="button" onClick={() => onNavigate('schedule')} className="px-3 py-2 rounded-lg bg-emerald-500 text-slate-950 text-xs font-semibold">Browse classes</button>
          )}
        </div>
      ) : (
        <div className="rounded-2xl glass-panel border border-slate-800 divide-y divide-slate-800/70">
          {bookings.map((booking) => {
            const classInfo = booking.fitness_class;
            const statusLabel = booking.status.replace('_', ' ');
            return (
              <article key={booking.id} className="p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="space-y-2 min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <h2 className="font-semibold text-sm text-white">{classInfo.title}</h2>
                    <span className={`px-2 py-0.5 rounded-full border text-[10px] font-semibold capitalize ${STATUS_STYLES[booking.status] || STATUS_STYLES.cancelled}`}>
                      {statusLabel}
                    </span>
                    {classInfo.is_cancelled && (
                      <span className="px-2 py-0.5 rounded-full border border-rose-500/20 bg-rose-500/10 text-[10px] font-semibold text-rose-300">
                        Class cancelled
                      </span>
                    )}
                    <span className="text-[10px] text-slate-400">{classInfo.category} · {classInfo.class_type}</span>
                  </div>
                  <div className="flex flex-wrap gap-x-4 gap-y-1 text-[11px] text-slate-400">
                    <span className="inline-flex items-center gap-1"><Calendar className="w-3.5 h-3.5" />{formatDate(classInfo.start_time)}</span>
                    <span className="inline-flex items-center gap-1"><MapPin className="w-3.5 h-3.5" />{classInfo.location_name}</span>
                    <span className="inline-flex items-center gap-1"><UserRound className="w-3.5 h-3.5" />{classInfo.trainer_name}</span>
                    <span className="inline-flex items-center gap-1"><Clock className="w-3.5 h-3.5" />Booked {formatDate(booking.booked_at)}</span>
                  </div>
                </div>
                {isMember && booking.status === 'booked' && (
                  <button
                    type="button"
                    onClick={() => handleCancel(booking.id)}
                    disabled={cancelingId === booking.id}
                    className="inline-flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg border border-rose-500/30 text-rose-300 hover:bg-rose-500/10 text-xs disabled:opacity-50 shrink-0"
                  >
                    <XCircle className="w-3.5 h-3.5" />
                    {cancelingId === booking.id ? 'Cancelling...' : 'Cancel booking'}
                  </button>
                )}
              </article>
            );
          })}
        </div>
      )}
    </div>
  );
}
