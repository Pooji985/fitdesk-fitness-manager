import React, { useState, useEffect, useMemo } from 'react';
import { useAuth } from '../context/AuthContext';
import { classService } from '../services/classService';
import { bookingService } from '../services/bookingService';
import WeatherBadge from '../components/WeatherBadge';
import ScheduleClassModal from '../components/ScheduleClassModal';
import {
  CalendarDays,
  CloudSun,
  Filter,
  Plus,
  Clock,
  MapPin,
  Users,
  Search,
  RefreshCw,
  Building2,
  Sparkles,
  AlertTriangle,
  CheckCircle2,
  ShieldAlert,
  SlidersHorizontal,
  X,
  Compass,
  Pencil,
  Ban,
  Info,
} from 'lucide-react';

const CATEGORY_OPTIONS = [
  'All',
  'Bootcamp',
  'HIIT',
  'Yoga',
  'Running',
  'Strength',
  'Cardio',
];

export default function Schedule() {
  const { user, isAdmin, isTrainer, isMember, isAuthenticated } = useAuth();

  const [classes, setClasses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters State
  const [selectedType, setSelectedType] = useState('all'); // 'all' | 'indoor' | 'outdoor'
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [selectedTrainerId, setSelectedTrainerId] = useState('');
  const [upcomingOnly, setUpcomingOnly] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [trainers, setTrainers] = useState([]);

  // Modal State
  const [modalOpen, setModalOpen] = useState(false);
  const [editingClass, setEditingClass] = useState(null);
  const [successToast, setSuccessToast] = useState(null);
  const [bookedClassIds, setBookedClassIds] = useState(new Set());
  const [bookingInProgressId, setBookingInProgressId] = useState(null);
  const [bookingError, setBookingError] = useState('');
  const [classActionError, setClassActionError] = useState('');
  const [cancelingClassId, setCancelingClassId] = useState(null);

  const fetchClasses = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await classService.getClasses({
        class_type: selectedType !== 'all' ? selectedType : undefined,
        category: selectedCategory !== 'All' ? selectedCategory : undefined,
        trainer_id: selectedTrainerId || undefined,
        upcoming_only: upcomingOnly,
        search: searchTerm.trim() ? searchTerm.trim() : undefined,
      });
      setClasses(data);
    } catch (err) {
      setError(err.message || 'Failed to load fitness classes from FastAPI.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchClasses();
  }, [selectedType, selectedCategory, selectedTrainerId, upcomingOnly]);

  useEffect(() => {
    let isMounted = true;
    classService.getTrainers()
      .then((records) => {
        if (isMounted) setTrainers(records.filter((trainer) => trainer.role === 'trainer'));
      })
      .catch((err) => {
        if (isMounted) setClassActionError(err.message || 'Could not load trainer filter options.');
      });
    return () => { isMounted = false; };
  }, []);

  useEffect(() => {
    let isMounted = true;
    if (!isAuthenticated || !isMember) {
      setBookedClassIds(new Set());
      return () => { isMounted = false; };
    }

    bookingService.getMyBookings()
      .then((bookings) => {
        if (isMounted) {
          setBookedClassIds(new Set(bookings.filter((booking) => booking.status !== 'cancelled').map((booking) => booking.class_id)));
        }
      })
      .catch((err) => {
        if (isMounted) setBookingError(err.message || 'Could not load your booking status.');
      });

    return () => { isMounted = false; };
  }, [isAuthenticated, isMember, user.id]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    fetchClasses();
  };

  const handleResetFilters = () => {
    setSelectedType('all');
    setSelectedCategory('All');
    setSelectedTrainerId('');
    setUpcomingOnly(false);
    setSearchTerm('');
  };

  const handleClassCreated = (newClass) => {
    setSuccessToast(`Class "${newClass.title}" scheduled successfully!`);
    fetchClasses();
    setTimeout(() => {
      setSuccessToast(null);
    }, 4500);
  };

  const handleClassUpdated = (updatedClass) => {
    setEditingClass(null);
    setSuccessToast(`Class "${updatedClass.title}" updated.`);
    fetchClasses();
    setTimeout(() => setSuccessToast(null), 4500);
  };

  const closeClassModal = () => {
    setModalOpen(false);
    setEditingClass(null);
  };

  const handleCancelClass = async (fitnessClass) => {
    const confirmed = window.confirm(
      `Cancel "${fitnessClass.title}"? Existing bookings and attendance history will be preserved.`,
    );
    if (!confirmed) return;

    setCancelingClassId(fitnessClass.id);
    setClassActionError('');
    try {
      await classService.cancelClass(fitnessClass.id);
      setSuccessToast(`Class "${fitnessClass.title}" cancelled. Existing bookings remain in member history.`);
      await fetchClasses();
      setTimeout(() => setSuccessToast(null), 5000);
    } catch (err) {
      setClassActionError(err.data?.detail || err.message || 'Could not cancel this class.');
    } finally {
      setCancelingClassId(null);
    }
  };

  const handleBookClass = async (fitnessClass) => {
    setBookingInProgressId(fitnessClass.id);
    setBookingError('');
    try {
      await bookingService.createBooking(fitnessClass.id);
      setBookedClassIds((currentIds) => new Set(currentIds).add(fitnessClass.id));
      setSuccessToast(`Booked ${fitnessClass.title}.`);
      await fetchClasses();
      setTimeout(() => setSuccessToast(null), 4500);
    } catch (err) {
      setBookingError(err.data?.detail || err.message || 'Could not book this class.');
    } finally {
      setBookingInProgressId(null);
    }
  };

  // Weather condition metrics summary
  const weatherSummary = useMemo(() => {
    const outdoor = classes.filter((c) => c.class_type === 'outdoor' && c.weather);
    const inclement = outdoor.filter((c) => c.weather?.status === 'inclement');
    const warnings = outdoor.filter((c) => c.weather?.status === 'warning');
    const optimal = outdoor.filter((c) => c.weather?.status === 'optimal');

    return {
      totalOutdoor: outdoor.length,
      inclementCount: inclement.length,
      warningCount: warnings.length,
      optimalCount: optimal.length,
      unavailableCount: outdoor.filter((c) => c.weather?.status === 'unavailable').length,
      hasSevereWeather: inclement.length > 0,
      hasWarning: warnings.length > 0,
    };
  }, [classes]);

  const formatClassTime = (startStr, endStr) => {
    try {
      const start = new Date(startStr);
      const end = new Date(endStr);
      const dateFormatted = start.toLocaleDateString('en-US', {
        weekday: 'short',
        month: 'short',
        day: 'numeric',
      });
      const timeFormatted = `${start.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
      })} - ${end.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
      })}`;
      return { dateFormatted, timeFormatted };
    } catch {
      return { dateFormatted: 'Scheduled', timeFormatted: 'Time TBD' };
    }
  };

  const hasActiveFilters = selectedType !== 'all'
    || selectedCategory !== 'All'
    || selectedTrainerId !== ''
    || upcomingOnly
    || searchTerm.trim() !== '';

  return (
    <div className="space-y-6">
      {/* Success Notification Toast */}
      {successToast && (
        <div className="fixed top-20 right-6 z-50 p-4 rounded-2xl bg-emerald-950/90 border border-emerald-500/40 text-emerald-300 shadow-2xl flex items-center gap-3 animate-fade-in backdrop-blur-md">
          <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
          <p className="text-xs font-semibold">{successToast}</p>
          <button
            onClick={() => setSuccessToast(null)}
            className="p-1 rounded-lg hover:bg-emerald-900/50 text-emerald-400 text-xs ml-2 cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}
      {bookingError && (
        <div role="alert" className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center justify-between gap-3">
          <span>{bookingError}</span>
          <button type="button" onClick={() => setBookingError('')} aria-label="Dismiss booking error"><X className="w-4 h-4" /></button>
        </div>
      )}
      {classActionError && (
        <div role="alert" className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center justify-between gap-3">
          <span>{classActionError}</span>
          <button type="button" onClick={() => setClassActionError('')} aria-label="Dismiss class action error"><X className="w-4 h-4" /></button>
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 mb-2">
            <CloudSun className="w-3.5 h-3.5" />
            <span>Open-Meteo Weather-Aware Timetable</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            Fitness Classes & Schedule
          </h1>
          <p className="text-xs sm:text-sm text-slate-400">
            Browse indoor studios and outdoor venues with live meteorological forecasting and capacity tracking.
          </p>
        </div>

        {/* Schedule New Class Action: Restricted to Admin and Trainer */}
        {isAuthenticated && isAdmin && (
          <button
            onClick={() => { setEditingClass(null); setModalOpen(true); }}
            className="flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl text-xs font-semibold bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-slate-950 transition-all shadow-lg shadow-emerald-500/20 cursor-pointer self-start sm:self-auto shrink-0"
          >
            <Plus className="w-4 h-4" />
            <span>Schedule New Class</span>
          </button>
        )}
      </div>

      {/* Stage 4 Live Meteorological Status Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Metric 1: Scheduled Classes */}
        <div className="p-4 rounded-2xl glass-card border border-slate-800/80 flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">
              Active Timetable
            </span>
            <p className="text-2xl font-bold text-white">{classes.length} Sessions</p>
            <p className="text-[11px] text-slate-500">Live SQLite Database</p>
          </div>
          <div className="p-3 rounded-xl bg-purple-500/10 text-purple-400">
            <CalendarDays className="w-5 h-5" />
          </div>
        </div>

        {/* Metric 2: Outdoor Weather Monitoring */}
        <div className="p-4 rounded-2xl glass-card border border-slate-800/80 flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">
              Outdoor Venues
            </span>
            <p className="text-2xl font-bold text-cyan-400">{weatherSummary.totalOutdoor} Monitored</p>
            <p className="text-[11px] text-cyan-400/70 font-mono">Open-Meteo API Synced</p>
          </div>
          <div className="p-3 rounded-xl bg-cyan-500/10 text-cyan-400">
            <CloudSun className="w-5 h-5" />
          </div>
        </div>

        {/* Metric 3: Weather Advisory Status */}
        <div
          className={`p-4 rounded-2xl border flex items-center justify-between ${
            weatherSummary.hasSevereWeather
              ? 'bg-rose-950/20 border-rose-500/30 text-rose-300'
              : weatherSummary.hasWarning
              ? 'bg-amber-950/20 border-amber-500/30 text-amber-300'
              : weatherSummary.unavailableCount > 0
              ? 'bg-slate-800/70 border-slate-600/50 text-slate-300'
              : 'glass-card border-emerald-500/30 text-emerald-300'
          }`}
        >
          <div className="space-y-1">
            <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">
              Meteorological Status
            </span>
            <p className="text-lg font-bold">
              {weatherSummary.hasSevereWeather
                ? 'Relocation Needed'
                : weatherSummary.hasWarning
                ? 'Weather Warning'
                : weatherSummary.unavailableCount > 0
                ? 'Forecast Unavailable'
                : weatherSummary.totalOutdoor === 0
                ? 'No outdoor classes'
                : 'Optimal Outdoors'}
            </p>
            <p className="text-[11px] text-slate-400">
              {weatherSummary.hasSevereWeather
                ? `${weatherSummary.inclementCount} outdoor class needs backup studio`
                : weatherSummary.hasWarning
                ? `${weatherSummary.warningCount} outdoor class advisory active`
                : weatherSummary.unavailableCount > 0
                ? `${weatherSummary.unavailableCount} forecast unavailable; check manually`
                : weatherSummary.totalOutdoor === 0
                ? 'Outdoor forecasts appear when outdoor classes are shown'
                : 'Mild temperatures & safe conditions'}
            </p>
          </div>
          <div
            className={`p-3 rounded-xl ${
              weatherSummary.hasSevereWeather
                ? 'bg-rose-500/20 text-rose-400'
                : weatherSummary.hasWarning
                ? 'bg-amber-500/20 text-amber-400'
                : weatherSummary.unavailableCount > 0 || weatherSummary.totalOutdoor === 0
                ? 'bg-slate-600/20 text-slate-300'
                : 'bg-emerald-500/10 text-emerald-400'
            }`}
          >
            {weatherSummary.hasSevereWeather ? (
              <ShieldAlert className="w-5 h-5" />
            ) : (weatherSummary.unavailableCount > 0 || weatherSummary.totalOutdoor === 0) && !weatherSummary.hasWarning ? (
              <Info className="w-5 h-5" />
            ) : (
              <CheckCircle2 className="w-5 h-5" />
            )}
          </div>
        </div>
      </div>

      {/* Filter and Search Controls */}
      <div className="p-4 rounded-2xl glass-panel border border-slate-800 space-y-4">
        <div className="flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-4">
          {/* Class Environment Toggle (All / Indoor / Outdoor) */}
          <div className="inline-flex p-1 rounded-xl bg-slate-950 border border-slate-800 self-start sm:self-auto">
            <button
              onClick={() => setSelectedType('all')}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                selectedType === 'all'
                  ? 'bg-emerald-500 text-slate-950 shadow-md'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              All Sessions
            </button>
            <button
              onClick={() => setSelectedType('outdoor')}
              className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                selectedType === 'outdoor'
                  ? 'bg-cyan-500 text-slate-950 shadow-md'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <CloudSun className="w-3.5 h-3.5" />
              <span>Outdoor Venues</span>
            </button>
            <button
              onClick={() => setSelectedType('indoor')}
              className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                selectedType === 'indoor'
                  ? 'bg-purple-500 text-slate-950 shadow-md'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Building2 className="w-3.5 h-3.5" />
              <span>Indoor Studios</span>
            </button>
          </div>

          {/* Search Bar & Category Filter */}
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
            {/* Category Select */}
            <div className="relative">
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="w-full sm:w-auto px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-300 text-xs focus:outline-none focus:border-emerald-500 cursor-pointer"
              >
                {CATEGORY_OPTIONS.map((cat) => (
                  <option key={cat} value={cat}>
                    Category: {cat}
                  </option>
                ))}
              </select>
            </div>

            <div className="relative">
              <select
                value={selectedTrainerId}
                onChange={(event) => setSelectedTrainerId(event.target.value)}
                className="w-full sm:w-auto px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-300 text-xs focus:outline-none focus:border-emerald-500 cursor-pointer"
              >
                <option value="">All trainers</option>
                {trainers.map((trainer) => (
                  <option key={trainer.id} value={trainer.id}>{trainer.name}</option>
                ))}
              </select>
            </div>

            <label className="inline-flex items-center gap-2 px-2.5 py-2 rounded-xl border border-slate-800 bg-slate-950 text-xs text-slate-300 cursor-pointer">
              <input type="checkbox" checked={upcomingOnly} onChange={(event) => setUpcomingOnly(event.target.checked)} />
              Upcoming only
            </label>

            {/* Keyword Search */}
            <form onSubmit={handleSearchSubmit} className="relative flex-1 sm:w-64">
              <input
                type="text"
                placeholder="Search class or venue..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-9 pr-4 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 placeholder:text-slate-600 text-xs focus:outline-none focus:border-emerald-500"
              />
              <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
            </form>

            {/* Refresh Button */}
            <button
              onClick={fetchClasses}
              disabled={loading}
              className="p-2 rounded-xl bg-slate-950 border border-slate-800 hover:border-slate-700 text-slate-400 hover:text-slate-200 transition-colors disabled:opacity-50 cursor-pointer"
              title="Refresh Timetable"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-emerald-400' : ''}`} />
            </button>

            {/* Clear Filters */}
            {hasActiveFilters && (
              <button
                onClick={handleResetFilters}
                className="px-3 py-2 rounded-xl text-xs text-rose-400 hover:text-rose-300 bg-rose-500/10 border border-rose-500/20 transition-colors cursor-pointer"
              >
                Reset Filters
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Main Class Grid */}
      {loading && classes.length === 0 ? (
        /* Loading Skeletons */
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div
              key={i}
              className="p-5 rounded-2xl glass-card border border-slate-800 animate-pulse space-y-4"
            >
              <div className="flex justify-between items-center">
                <div className="h-5 w-20 bg-slate-800 rounded-full"></div>
                <div className="h-4 w-28 bg-slate-800 rounded"></div>
              </div>
              <div className="h-6 w-3/4 bg-slate-800 rounded"></div>
              <div className="h-4 w-1/2 bg-slate-800 rounded"></div>
              <div className="h-16 bg-slate-800/60 rounded-xl"></div>
              <div className="h-10 bg-slate-800/40 rounded-xl"></div>
            </div>
          ))}
        </div>
      ) : error ? (
        /* Error State */
        <div className="p-6 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-300 flex items-start justify-between gap-4">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-rose-200 text-sm">Failed to Load Schedule</p>
              <p className="text-xs text-rose-300/80 mt-1">{error}</p>
            </div>
          </div>
          <button
            onClick={fetchClasses}
            className="px-3.5 py-1.5 rounded-xl bg-slate-900 border border-rose-500/30 text-rose-300 text-xs font-semibold hover:bg-slate-800 transition-colors cursor-pointer shrink-0"
          >
            Retry
          </button>
        </div>
      ) : classes.length === 0 ? (
        /* Empty State */
        <div className="p-12 text-center rounded-2xl glass-card border border-slate-800 space-y-3">
          <CalendarDays className="w-10 h-10 text-slate-600 mx-auto" />
          <h3 className="font-bold text-base text-slate-200">No Scheduled Classes Found</h3>
          <p className="text-xs text-slate-400 max-w-md mx-auto">
            {hasActiveFilters
              ? 'No classes match your current filter selections. Try clearing your filters or changing categories.'
              : 'There are currently no fitness classes scheduled in the system.'}
          </p>
          {hasActiveFilters ? (
            <button
              onClick={handleResetFilters}
              className="mt-2 px-4 py-2 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 transition-colors cursor-pointer"
            >
              Clear Active Filters
            </button>
          ) : (
            isAuthenticated && isAdmin && (
              <button
                onClick={() => { setEditingClass(null); setModalOpen(true); }}
                className="mt-2 px-4 py-2 rounded-xl text-xs font-semibold bg-emerald-500 hover:bg-emerald-400 text-slate-950 transition-colors cursor-pointer"
              >
                Schedule First Class
              </button>
            )
          )}
        </div>
      ) : (
        /* Class Cards Grid */
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {classes.map((cls) => {
            const isOutdoor = cls.class_type === 'outdoor';
            const { dateFormatted, timeFormatted } = formatClassTime(cls.start_time, cls.end_time);
            const occupancyPct = Math.round((cls.booked_count / cls.capacity) * 100);
            const isFull = cls.remaining_spots === 0;
            const hasStarted = new Date(cls.start_time) <= new Date();

            return (
              <div
                key={cls.id}
                className="p-5 rounded-3xl glass-card border border-slate-800/90 hover:border-slate-700 transition-all duration-300 flex flex-col justify-between space-y-4 hover:shadow-xl hover:shadow-slate-950/50"
              >
                {/* Top Badge & Time Row */}
                <div className="space-y-2.5">
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      {/* Environment Badge */}
                      <span
                        className={`inline-flex items-center gap-1 text-[11px] font-bold px-2.5 py-0.5 rounded-full border ${
                          isOutdoor
                            ? 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20'
                            : 'bg-purple-500/10 text-purple-400 border-purple-500/20'
                        }`}
                      >
                        {isOutdoor ? (
                          <CloudSun className="w-3 h-3" />
                        ) : (
                          <Building2 className="w-3 h-3" />
                        )}
                        <span>{isOutdoor ? 'Outdoor' : 'Indoor'}</span>
                      </span>

                      {/* Discipline Badge */}
                      <span className="text-[10px] font-semibold px-2 py-0.5 rounded-md bg-slate-800 text-slate-300 border border-slate-700">
                        {cls.category}
                      </span>
                    </div>

                    {/* Date Badge */}
                    <span className="text-[11px] font-medium text-slate-400">
                      {dateFormatted}
                    </span>
                  </div>

                  {/* Title & Description */}
                  <div>
                    <h3 className="font-bold text-base text-white group-hover:text-emerald-400 transition-colors">
                      {cls.title}
                    </h3>
                    <p className="text-xs text-slate-400 line-clamp-2 mt-1 leading-relaxed">
                      {cls.description || 'Full coaching session tailored to build conditioning and endurance.'}
                    </p>
                  </div>

                  {/* Time & Venue Info */}
                  <div className="pt-2 space-y-1.5 text-xs text-slate-400">
                    <div className="flex items-center gap-2">
                      <Clock className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                      <span className="font-mono text-[11px] text-slate-300">{timeFormatted}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <MapPin className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                      <span className="truncate">{cls.location_name}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Users className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                      <span>Coach: {cls.trainer_name || 'Assigned Trainer'}</span>
                    </div>
                  </div>
                </div>

                {/* Bottom Section: Capacity Gauge & Open-Meteo Weather Badge */}
                <div className="pt-3 border-t border-slate-800/80 space-y-3">
                  {/* Capacity Bar */}
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="text-slate-400">
                        Attendance ({cls.booked_count}/{cls.capacity})
                      </span>
                      <span
                        className={`font-semibold ${
                          isFull
                            ? 'text-rose-400'
                            : cls.remaining_spots <= 3
                            ? 'text-amber-400'
                            : 'text-emerald-400'
                        }`}
                      >
                        {isFull ? 'Session Full' : `${cls.remaining_spots} spots left`}
                      </span>
                    </div>
                    <div className="w-full h-1.5 bg-slate-950 rounded-full overflow-hidden border border-slate-800">
                      <div
                        className={`h-full rounded-full transition-all duration-500 ${
                          isFull
                            ? 'bg-rose-500'
                            : occupancyPct > 75
                            ? 'bg-amber-400'
                            : 'bg-emerald-500'
                        }`}
                        style={{ width: `${Math.min(occupancyPct, 100)}%` }}
                      ></div>
                    </div>
                  </div>

                  {/* Weather Forecast (Stage 4 Core Feature) */}
                  {isOutdoor ? (
                    cls.weather ? (
                      <WeatherBadge weather={cls.weather} />
                    ) : (
                      <div className="p-2.5 rounded-xl bg-slate-900 border border-slate-800 text-[11px] text-slate-400 flex items-center gap-2">
                        <CloudSun className="w-3.5 h-3.5 text-cyan-400" />
                        <span>Querying Open-Meteo satellite forecast...</span>
                      </div>
                    )
                  ) : (
                    /* Indoor Studio Badge */
                    <div className="p-2 rounded-xl bg-slate-950/60 border border-slate-800/80 text-[11px] text-slate-400 flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Building2 className="w-3.5 h-3.5 text-purple-400" />
                        <span>Indoor Studio • Climate Controlled</span>
                      </div>
                      <span className="text-[10px] text-slate-500 font-mono">AC Active</span>
                    </div>
                  )}

                  {isMember && (
                    isAuthenticated ? (
                      <button
                        type="button"
                        onClick={() => handleBookClass(cls)}
                        disabled={isFull || hasStarted || bookedClassIds.has(cls.id) || bookingInProgressId === cls.id}
                        className="w-full inline-flex items-center justify-center gap-2 px-3 py-2 rounded-lg bg-emerald-500 text-slate-950 text-xs font-semibold hover:bg-emerald-400 disabled:bg-slate-800 disabled:text-slate-400 disabled:cursor-not-allowed"
                      >
                        {bookingInProgressId === cls.id ? 'Booking...' : bookedClassIds.has(cls.id) ? 'Already booked' : hasStarted ? 'Booking closed' : isFull ? 'Class full' : 'Book class'}
                      </button>
                    ) : (
                      <p className="text-center text-[11px] text-slate-500">Sign in as a member to book this class.</p>
                    )
                  )}

                  {isAuthenticated && isAdmin && (
                    <div className="flex gap-2 pt-1">
                      <button
                        type="button"
                        onClick={() => { setEditingClass(cls); setModalOpen(true); }}
                        className="flex-1 inline-flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg border border-slate-700 text-slate-300 hover:bg-slate-800 text-xs font-medium"
                      >
                        <Pencil className="w-3.5 h-3.5" /> Edit class
                      </button>
                      <button
                        type="button"
                        onClick={() => handleCancelClass(cls)}
                        disabled={cancelingClassId === cls.id}
                        className="flex-1 inline-flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg border border-rose-500/30 text-rose-300 hover:bg-rose-500/10 text-xs font-medium disabled:opacity-50"
                      >
                        <Ban className="w-3.5 h-3.5" />
                        {cancelingClassId === cls.id ? 'Cancelling...' : 'Cancel class'}
                      </button>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Schedule Class Modal */}
      <ScheduleClassModal
        isOpen={modalOpen}
        onClose={closeClassModal}
        onClassCreated={handleClassCreated}
        editingClass={editingClass}
        onClassUpdated={handleClassUpdated}
      />
    </div>
  );
}
