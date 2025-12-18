import { Globe, TrendingUp, MapPin } from 'lucide-react';

interface Country {
  code: string;
  name: string;
  score: number;
  region: string;
}

const countries: Country[] = [
  { code: 'US', name: 'United States', score: 92, region: 'North America' },
  { code: 'SG', name: 'Singapore', score: 88, region: 'Asia Pacific' },
  { code: 'UK', name: 'United Kingdom', score: 85, region: 'Europe' },
  { code: 'DE', name: 'Germany', score: 83, region: 'Europe' },
  { code: 'CA', name: 'Canada', score: 81, region: 'North America' },
  { code: 'JP', name: 'Japan', score: 79, region: 'Asia Pacific' },
  { code: 'AU', name: 'Australia', score: 77, region: 'Asia Pacific' },
  { code: 'FR', name: 'France', score: 75, region: 'Europe' },
  { code: 'KR', name: 'South Korea', score: 74, region: 'Asia Pacific' },
  { code: 'NL', name: 'Netherlands', score: 72, region: 'Europe' },
  { code: 'SE', name: 'Sweden', score: 70, region: 'Europe' },
  { code: 'CH', name: 'Switzerland', score: 68, region: 'Europe' }
];

export function CountryMap() {
  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center gap-3">
        <Globe className="w-5 h-5 text-blue-400" />
        <h2 className="text-muted-foreground uppercase tracking-wider text-sm">
          Country Analysis
        </h2>
      </div>
      
      <div className="grid grid-cols-2 gap-3 max-h-[500px] overflow-y-auto pr-2 custom-scrollbar">
        {countries.map((country) => (
          <div
            key={country.code}
            className="relative group px-4 py-3 rounded-xl bg-slate-800/30 border border-slate-700/50 hover:border-blue-500/50 hover:bg-slate-800/50 transition-all duration-300 cursor-pointer"
          >
            <div className="flex items-start justify-between gap-3">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <MapPin className="w-3.5 h-3.5 text-blue-400 flex-shrink-0" />
                  <span className="text-sm text-foreground/90 truncate">
                    {country.name}
                  </span>
                </div>
                <div className="text-xs text-muted-foreground">
                  {country.region}
                </div>
              </div>
              
              <div className="flex flex-col items-end gap-1 flex-shrink-0">
                <div className="flex items-center gap-1">
                  <TrendingUp className="w-3 h-3 text-emerald-400" />
                  <span className="text-sm text-emerald-400">
                    {country.score}
                  </span>
                </div>
                
                {/* Score bar */}
                <div className="w-16 h-1.5 bg-slate-700/50 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-gradient-to-r from-blue-500 to-emerald-500 rounded-full transition-all duration-500"
                    style={{ width: `${country.score}%` }}
                  />
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      <style>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 6px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: rgba(30, 41, 59, 0.3);
          border-radius: 3px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: rgba(59, 130, 246, 0.3);
          border-radius: 3px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: rgba(59, 130, 246, 0.5);
        }
      `}</style>
    </div>
  );
}
