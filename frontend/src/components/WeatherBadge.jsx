import React from 'react';
import {
  Sun,
  CloudSun,
  CloudRain,
  CloudLightning,
  Wind,
  Droplets,
  AlertTriangle,
  Info,
} from 'lucide-react';

export default function WeatherBadge({ weather, compact = false }) {
  if (!weather) return null;

  if (weather.status === 'unavailable') {
    return (
      <div role="status" className="p-2.5 rounded-xl border border-slate-600/50 bg-slate-500/10 text-slate-300 text-[11px] flex items-center gap-2">
        <Info className="w-4 h-4 shrink-0" />
        <span>Weather unavailable — check manually.</span>
      </div>
    );
  }

  const isInclement = weather.status === 'inclement';
  const isWarning = weather.status === 'warning';
  // Choose icon based on condition & status
  let WeatherIcon = CloudSun;
  if (isInclement) {
    WeatherIcon = CloudLightning;
  } else if (isWarning || weather.precipitation_probability > 30) {
    WeatherIcon = CloudRain;
  } else if (weather.condition.toLowerCase().includes('clear') || weather.condition.toLowerCase().includes('sun')) {
    WeatherIcon = Sun;
  }

  // Visual status pill colors
  const statusStyles = isInclement
    ? {
        border: 'border-rose-500/30',
        bg: 'bg-rose-500/10',
        text: 'text-rose-400',
        indicator: 'bg-rose-500',
        label: 'Inclement Weather',
        banner: 'bg-rose-950/40 border-rose-500/30 text-rose-300',
      }
    : isWarning
    ? {
        border: 'border-amber-500/30',
        bg: 'bg-amber-500/10',
        text: 'text-amber-400',
        indicator: 'bg-amber-500',
        label: 'Weather Warning',
        banner: 'bg-amber-950/40 border-amber-500/30 text-amber-300',
      }
    : {
        border: 'border-emerald-500/30',
        bg: 'bg-emerald-500/10',
        text: 'text-emerald-400',
        indicator: 'bg-emerald-400',
        label: 'Optimal Weather',
        banner: 'bg-emerald-950/30 border-emerald-500/20 text-emerald-300',
      };

  if (compact) {
    return (
      <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-medium border ${statusStyles.bg} ${statusStyles.border} ${statusStyles.text}`}>
        <span className={`w-1.5 h-1.5 rounded-full ${statusStyles.indicator} animate-pulse`}></span>
        <WeatherIcon className="w-3.5 h-3.5" />
        <span className="font-semibold">{Math.round(weather.temperature)}°C</span>
        <span className="text-slate-400">•</span>
        <span>{weather.condition}</span>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {/* Weather Header Pill */}
      <div className={`p-2.5 rounded-xl border ${statusStyles.bg} ${statusStyles.border} flex items-center justify-between gap-3 text-xs`}>
        <div className="flex items-center gap-2">
          <div className={`p-1.5 rounded-lg bg-slate-900/60 ${statusStyles.text}`}>
            <WeatherIcon className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className={`w-1.5 h-1.5 rounded-full ${statusStyles.indicator}`}></span>
              <span className={`font-bold text-[11px] uppercase tracking-wider ${statusStyles.text}`}>
                {statusStyles.label}
              </span>
            </div>
            <p className="text-[12px] font-semibold text-slate-200 mt-0.5">
              {Math.round(weather.temperature)}°C • {weather.condition}
            </p>
          </div>
        </div>

        {/* Quick Weather Metrics */}
        <div className="flex items-center gap-3 text-[11px] font-mono text-slate-400">
          <span className="flex items-center gap-1" title="Precipitation Probability">
            <Droplets className="w-3 h-3 text-cyan-400" />
            {weather.precipitation_probability}%
          </span>
          <span className="flex items-center gap-1" title="Wind Speed">
            <Wind className="w-3 h-3 text-slate-400" />
            {Math.round(weather.wind_speed)} km/h
          </span>
        </div>
      </div>

      {/* Advisory Message Banner for Warning or Inclement */}
      {(isWarning || isInclement) && weather.alert_message && (
        <div className={`p-2 rounded-lg border text-[11px] flex items-start gap-2 ${statusStyles.banner}`}>
          <AlertTriangle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
          <span>{weather.alert_message}</span>
        </div>
      )}
    </div>
  );
}
