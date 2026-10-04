import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { classService } from '../services/classService';
import {
  X,
  Calendar,
  Clock,
  MapPin,
  Users,
  Dumbbell,
  CloudSun,
  Building2,
  AlertTriangle,
  CheckCircle2,
  Sparkles,
  Compass,
} from 'lucide-react';

const CATEGORIES = [
  'Bootcamp',
  'HIIT',
  'Yoga',
  'Running',
  'Strength',
  'Cardio',
  'Pilates',
  'Mobility',
];

const OUTDOOR_PRESETS = [
  {
    name: 'Central Park West Field',
    lat: 40.785091,
    lon: -73.968285,
  },
  {
    name: 'Riverside Park Trailhead',
    lat: 40.801000,
    lon: -73.971000,
  },
  {
    name: 'Hudson River Park Pier 45',
    lat: 40.733000,
    lon: -74.012000,
  },
  {
    name: 'Prospect Park Meadow',
    lat: 40.660200,
    lon: -73.968900,
  },
];

function getLocalDateTimeParts(value) {
  const dateTime = new Date(value);
  const localDateTime = new Date(dateTime.getTime() - dateTime.getTimezoneOffset() * 60000).toISOString();
  return { date: localDateTime.slice(0, 10), time: localDateTime.slice(11, 16) };
}

export default function ScheduleClassModal({ isOpen, onClose, onClassCreated, editingClass = null, onClassUpdated }) {
  const { user, isAdmin, isTrainer } = useAuth();

  const [trainers, setTrainers] = useState([]);
  const [loadingTrainers, setLoadingTrainers] = useState(false);

  // Form State
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState('Bootcamp');
  const [classType, setClassType] = useState('outdoor'); // 'indoor' | 'outdoor'
  const [locationName, setLocationName] = useState('Central Park West Field');
  const [latitude, setLatitude] = useState('40.785091');
  const [longitude, setLongitude] = useState('-73.968285');
  const [trainerId, setTrainerId] = useState(user.id || 2);
  const [capacity, setCapacity] = useState(20);
  
  // Date & Time state
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  const defaultDateStr = tomorrow.toISOString().split('T')[0];
  const [date, setDate] = useState(defaultDateStr);
  const [startTime, setStartTime] = useState('08:00');
  const [durationMinutes, setDurationMinutes] = useState(60);

  const [submitting, setSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);

  // Fetch trainers for Admin dropdown
  useEffect(() => {
    if (isOpen) {
      setErrorMessage(null);
      setLoadingTrainers(true);
      classService.getTrainers()
        .then((data) => {
          setTrainers(data);
          if (isTrainer) {
            setTrainerId(user.id);
          } else if (data.length > 0 && !trainerId) {
            setTrainerId(data[0].id);
          }
        })
        .catch((err) => {
          setErrorMessage(err.data?.detail || err.message || 'Failed to load trainers.');
        })
        .finally(() => setLoadingTrainers(false));
    }
  }, [isOpen, isTrainer, user.id]);

  useEffect(() => {
    if (!isOpen) return;
    if (!editingClass) {
      setTitle('');
      setDescription('');
      setCategory('Bootcamp');
      setClassType('outdoor');
      setLocationName(OUTDOOR_PRESETS[0].name);
      setLatitude(String(OUTDOOR_PRESETS[0].lat));
      setLongitude(String(OUTDOOR_PRESETS[0].lon));
      setTrainerId(user.id || 2);
      setCapacity(20);
      setDate(defaultDateStr);
      setStartTime('08:00');
      setDurationMinutes(60);
      return;
    }

    const startParts = getLocalDateTimeParts(editingClass.start_time);
    const duration = Math.round((new Date(editingClass.end_time) - new Date(editingClass.start_time)) / 60000);
    setTitle(editingClass.title);
    setDescription(editingClass.description || '');
    setCategory(editingClass.category);
    setClassType(editingClass.class_type);
    setLocationName(editingClass.location_name);
    setLatitude(editingClass.latitude == null ? '' : String(editingClass.latitude));
    setLongitude(editingClass.longitude == null ? '' : String(editingClass.longitude));
    setTrainerId(String(editingClass.trainer_id));
    setCapacity(editingClass.capacity);
    setDate(startParts.date);
    setStartTime(startParts.time);
    setDurationMinutes(duration);
  }, [isOpen, editingClass?.id]);

  if (!isOpen) return null;

  const handlePresetSelect = (preset) => {
    setLocationName(preset.name);
    setLatitude(preset.lat.toString());
    setLongitude(preset.lon.toString());
  };

  const handleTypeChange = (newType) => {
    setClassType(newType);
    if (newType === 'indoor') {
      setLocationName('Studio A (Main Gym)');
    } else {
      handlePresetSelect(OUTDOOR_PRESETS[0]);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage(null);

    // Basic validation
    if (!title.trim()) {
      setErrorMessage('Please provide a class title.');
      return;
    }
    if (!locationName.trim()) {
      setErrorMessage('Please specify a location or studio name.');
      return;
    }
    if (!date || !startTime) {
      setErrorMessage('Please select date and start time.');
      return;
    }

    try {
      setSubmitting(true);

      // Build start_time and end_time ISO strings
      const startDateTime = new Date(`${date}T${startTime}:00`);
      const endDateTime = new Date(startDateTime.getTime() + durationMinutes * 60 * 1000);

      const payload = {
        title: title.trim(),
        description: description.trim() || (editingClass ? null : undefined),
        category,
        class_type: classType,
        location_name: locationName.trim(),
        latitude: classType === 'outdoor' && latitude ? parseFloat(latitude) : undefined,
        longitude: classType === 'outdoor' && longitude ? parseFloat(longitude) : undefined,
        capacity: parseInt(capacity, 10) || 20,
        start_time: startDateTime.toISOString(),
        end_time: endDateTime.toISOString(),
        trainer_id: parseInt(trainerId, 10),
      };

      if (editingClass) {
        const updated = await classService.updateClass(editingClass.id, payload);
        onClassUpdated(updated);
      } else {
        const created = await classService.createClass(payload);
        onClassCreated(created);
      }
      onClose();
    } catch (err) {
      setErrorMessage(err.data?.detail || err.message || 'Failed to schedule new class.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fade-in overflow-y-auto">
      <div className="relative w-full max-w-2xl bg-slate-900 border border-slate-800 rounded-3xl shadow-2xl shadow-emerald-950/30 overflow-hidden my-8">
        {/* Header */}
        <div className="p-6 border-b border-slate-800/80 flex items-center justify-between bg-slate-900/50">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-2xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <Calendar className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">{editingClass ? 'Edit Fitness Class' : 'Schedule Fitness Class'}</h2>
              <p className="text-xs text-slate-400">
                {editingClass ? 'Update class details and schedule.' : 'Create a new indoor or weather-aware outdoor training session.'}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Error Alert */}
        {errorMessage && (
          <div className="mx-6 mt-4 p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 shrink-0 text-rose-400" />
            <span>{errorMessage}</span>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-5 text-xs max-h-[75vh] overflow-y-auto">
          {/* Class Title */}
          <div className="space-y-1.5">
            <label className="font-semibold text-slate-300">Class Title *</label>
            <input
              type="text"
              required
              placeholder="e.g. Sunrise Power Bootcamp"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 placeholder:text-slate-600 focus:outline-none focus:border-emerald-500 text-xs"
            />
          </div>

          {/* Environment & Category Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Class Type Toggle */}
            <div className="space-y-1.5">
              <label className="font-semibold text-slate-300">Environment</label>
              <div className="grid grid-cols-2 gap-2 p-1 rounded-xl bg-slate-950 border border-slate-800">
                <button
                  type="button"
                  onClick={() => handleTypeChange('outdoor')}
                  className={`flex items-center justify-center gap-1.5 py-2 rounded-lg font-semibold transition-all ${
                    classType === 'outdoor'
                      ? 'bg-emerald-500 text-slate-950 shadow-md'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  <CloudSun className="w-4 h-4" />
                  <span>Outdoor</span>
                </button>
                <button
                  type="button"
                  onClick={() => handleTypeChange('indoor')}
                  className={`flex items-center justify-center gap-1.5 py-2 rounded-lg font-semibold transition-all ${
                    classType === 'indoor'
                      ? 'bg-emerald-500 text-slate-950 shadow-md'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  <Building2 className="w-4 h-4" />
                  <span>Indoor</span>
                </button>
              </div>
            </div>

            {/* Category Select */}
            <div className="space-y-1.5">
              <label className="font-semibold text-slate-300">Discipline / Category</label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 focus:outline-none focus:border-emerald-500 text-xs"
              >
                {CATEGORIES.map((cat) => (
                  <option key={cat} value={cat}>
                    {cat}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Trainer Selection & Capacity Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Trainer Assignment */}
            <div className="space-y-1.5">
              <label className="font-semibold text-slate-300">Assigned Coach / Trainer</label>
              {isAdmin ? (
                <select
                  value={trainerId}
                  onChange={(e) => setTrainerId(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 focus:outline-none focus:border-emerald-500 text-xs"
                  disabled={loadingTrainers}
                >
                  {trainers.map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.name} ({t.role_title || 'Coach'})
                    </option>
                  ))}
                </select>
              ) : (
                <div className="px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-300 flex items-center justify-between">
                  <span>{user.name}</span>
                  <span className="text-[10px] text-emerald-400 font-semibold px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/20">
                    Lead Coach
                  </span>
                </div>
              )}
            </div>

            {/* Max Capacity */}
            <div className="space-y-1.5">
              <label className="font-semibold text-slate-300">Max Capacity</label>
              <input
                type="number"
                min="1"
                max="200"
                value={capacity}
                onChange={(e) => setCapacity(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 focus:outline-none focus:border-emerald-500 text-xs"
              />
            </div>
          </div>

          {/* Location Name */}
          <div className="space-y-1.5">
            <label className="font-semibold text-slate-300">
              {classType === 'outdoor' ? 'Outdoor Venue / Meeting Spot *' : 'Indoor Studio / Room *'}
            </label>
            <input
              type="text"
              required
              value={locationName}
              onChange={(e) => setLocationName(e.target.value)}
              placeholder={classType === 'outdoor' ? 'e.g. Central Park West Field' : 'e.g. Studio A'}
              className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 focus:outline-none focus:border-emerald-500 text-xs"
            />
          </div>

          {/* Outdoor Venue Presets and Coordinates (Only if outdoor) */}
          {classType === 'outdoor' && (
            <div className="p-4 rounded-2xl bg-cyan-950/20 border border-cyan-500/20 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5 text-cyan-300 font-semibold">
                  <Compass className="w-4 h-4 text-cyan-400" />
                  <span>Open-Meteo Weather Location Presets</span>
                </div>
                <span className="text-[10px] text-cyan-400/80">Auto-queries live forecast</span>
              </div>

              {/* Preset Buttons */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                {OUTDOOR_PRESETS.map((preset) => {
                  const isSelected = locationName === preset.name;
                  return (
                    <button
                      key={preset.name}
                      type="button"
                      onClick={() => handlePresetSelect(preset)}
                      className={`p-2 rounded-xl text-left border transition-all ${
                        isSelected
                          ? 'bg-cyan-500/20 border-cyan-400 text-cyan-200 font-bold'
                          : 'bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700'
                      }`}
                    >
                      <p className="truncate text-[11px]">{preset.name}</p>
                      <p className="text-[9px] text-slate-500 font-mono mt-0.5">
                        {preset.lat.toFixed(2)}, {preset.lon.toFixed(2)}
                      </p>
                    </button>
                  );
                })}
              </div>

              {/* Coordinates Inputs */}
              <div className="grid grid-cols-2 gap-3 pt-1">
                <div>
                  <label className="text-[10px] text-slate-400">Latitude</label>
                  <input
                    type="number"
                    step="0.000001"
                    value={latitude}
                    onChange={(e) => setLatitude(e.target.value)}
                    className="w-full mt-1 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-200 font-mono text-[11px] focus:outline-none focus:border-cyan-500"
                  />
                </div>
                <div>
                  <label className="text-[10px] text-slate-400">Longitude</label>
                  <input
                    type="number"
                    step="0.000001"
                    value={longitude}
                    onChange={(e) => setLongitude(e.target.value)}
                    className="w-full mt-1 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-200 font-mono text-[11px] focus:outline-none focus:border-cyan-500"
                  />
                </div>
              </div>
            </div>
          )}

          {/* Schedule Date, Time & Duration Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {/* Date */}
            <div className="space-y-1.5">
              <label className="font-semibold text-slate-300">Date *</label>
              <input
                type="date"
                required
                value={date}
                onChange={(e) => setDate(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 focus:outline-none focus:border-emerald-500 text-xs"
              />
            </div>

            {/* Start Time */}
            <div className="space-y-1.5">
              <label className="font-semibold text-slate-300">Start Time *</label>
              <input
                type="time"
                required
                value={startTime}
                onChange={(e) => setStartTime(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 focus:outline-none focus:border-emerald-500 text-xs"
              />
            </div>

            {/* Duration */}
            <div className="space-y-1.5">
              <label className="font-semibold text-slate-300">Duration</label>
              <select
                value={durationMinutes}
                onChange={(e) => setDurationMinutes(parseInt(e.target.value, 10))}
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 focus:outline-none focus:border-emerald-500 text-xs"
              >
                {[...new Set([45, 60, 75, 90, durationMinutes])].sort((a, b) => a - b).map((minutes) => (
                  <option key={minutes} value={minutes}>{minutes} Minutes{minutes === 60 ? ' (1 hr)' : minutes === 90 ? ' (1.5 hrs)' : ''}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Description */}
          <div className="space-y-1.5">
            <label className="font-semibold text-slate-300">Session Description</label>
            <textarea
              rows={2}
              placeholder="Outline workout goals, intensity, or equipment needed..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 placeholder:text-slate-600 focus:outline-none focus:border-emerald-500 text-xs resize-none"
            />
          </div>

          {/* Modal Actions */}
          <div className="pt-4 border-t border-slate-800/80 flex items-center justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              disabled={submitting}
              className="px-4 py-2.5 rounded-xl font-semibold text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="flex items-center gap-2 px-5 py-2.5 rounded-xl font-semibold bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-slate-950 shadow-lg shadow-emerald-500/20 transition-all disabled:opacity-50 cursor-pointer"
            >
              {submitting ? (
                <>
                  <span className="w-3.5 h-3.5 border-2 border-slate-950 border-t-transparent rounded-full animate-spin"></span>
                  <span>Scheduling...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  <span>{editingClass ? 'Save Changes' : 'Publish Class'}</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
