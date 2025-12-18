import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer } from 'recharts';
import { Info } from 'lucide-react';

interface CountryDetail {
  iso: string;
  country: string;
  rank: number;
  topsisScore: number;
  rcScore: number;
  gdpPerCapita: number;
  digitalInfra: number;
  jobMarket: number;
  description: string;
}

interface CountryDetailCardProps {
  countryDetail: CountryDetail | null;
}

export function CountryDetailCard({ countryDetail }: CountryDetailCardProps) {
  if (!countryDetail) {
    return (
      <div className="bg-slate-900/50 backdrop-blur-sm rounded-3xl p-8 border border-slate-800/50 shadow-2xl h-full flex items-center justify-center">
        <div className="text-center text-muted-foreground">
          <Info className="w-12 h-12 mx-auto mb-3 opacity-50" />
          <p>Select a country to view details</p>
        </div>
      </div>
    );
  }

  const radarData = [
    { metric: 'RC Score', value: countryDetail.rcScore, fullMark: 100 },
    { metric: 'GDP/Capita', value: (countryDetail.gdpPerCapita / 1000), fullMark: 100 },
    { metric: 'Digital Infra', value: countryDetail.digitalInfra, fullMark: 100 },
    { metric: 'Job Market', value: countryDetail.jobMarket, fullMark: 100 }
  ];

  return (
    <div className="bg-slate-900/50 backdrop-blur-sm rounded-3xl p-8 border border-slate-800/50 shadow-2xl">
      <div className="flex items-start justify-between mb-6">
        <div>
          <h3 className="text-2xl mb-1 text-foreground">{countryDetail.country}</h3>
          <div className="flex items-center gap-3">
            <span className="text-sm text-muted-foreground">Rank #{countryDetail.rank}</span>
            <span className="text-sm px-2 py-1 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
              Score: {countryDetail.topsisScore.toFixed(3)}
            </span>
          </div>
        </div>
        <div className="w-12 h-12 rounded-xl bg-blue-500/10 border border-blue-500/30 flex items-center justify-center text-blue-400">
          {countryDetail.iso}
        </div>
      </div>

      {/* Radar Chart */}
      <div className="mb-6 bg-slate-800/30 rounded-2xl p-4 border border-slate-700/30">
        <h4 className="text-sm text-muted-foreground uppercase tracking-wider mb-4">Metrics Overview</h4>
        <ResponsiveContainer width="100%" height={250}>
          <RadarChart data={radarData}>
            <PolarGrid stroke="#475569" strokeOpacity={0.3} />
            <PolarAngleAxis 
              dataKey="metric" 
              tick={{ fill: '#94a3b8', fontSize: 12 }}
            />
            <PolarRadiusAxis 
              angle={90} 
              domain={[0, 100]}
              tick={{ fill: '#64748b', fontSize: 10 }}
            />
            <Radar
              name={countryDetail.country}
              dataKey="value"
              stroke="#3b82f6"
              fill="#3b82f6"
              fillOpacity={0.3}
              strokeWidth={2}
            />
          </RadarChart>
        </ResponsiveContainer>
      </div>

      {/* Metric Details */}
      <div className="grid grid-cols-2 gap-3 mb-6">
        <div className="bg-slate-800/30 rounded-xl p-3 border border-slate-700/30">
          <div className="text-xs text-muted-foreground mb-1">Regulation Complexity</div>
          <div className="text-lg text-foreground">{countryDetail.rcScore.toFixed(2)}</div>
        </div>
        <div className="bg-slate-800/30 rounded-xl p-3 border border-slate-700/30">
          <div className="text-xs text-muted-foreground mb-1">GDP per Capita</div>
          <div className="text-lg text-foreground">${(countryDetail.gdpPerCapita / 1000).toFixed(0)}k</div>
        </div>
        <div className="bg-slate-800/30 rounded-xl p-3 border border-slate-700/30">
          <div className="text-xs text-muted-foreground mb-1">Digital Infrastructure</div>
          <div className="text-lg text-foreground">{countryDetail.digitalInfra.toFixed(2)}</div>
        </div>
        <div className="bg-slate-800/30 rounded-xl p-3 border border-slate-700/30">
          <div className="text-xs text-muted-foreground mb-1">Job Market Index</div>
          <div className="text-lg text-foreground">{countryDetail.jobMarket.toFixed(2)}</div>
        </div>
      </div>

      {/* Description */}
      <div className="bg-blue-500/5 border border-blue-500/20 rounded-xl p-4">
        <div className="flex items-start gap-2">
          <Info className="w-4 h-4 text-blue-400 mt-0.5 flex-shrink-0" />
          <p className="text-sm text-slate-300 leading-relaxed">
            {countryDetail.description}
          </p>
        </div>
      </div>
    </div>
  );
}
