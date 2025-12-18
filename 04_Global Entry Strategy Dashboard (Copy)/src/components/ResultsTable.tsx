interface CountryResult {
  rank: number;
  iso: string;
  country: string;
  topsisScore: number;
  rcScore: number;
  gdpPerCapita: number;
  digitalInfra: number;
  jobMarket: number;
}

interface ResultsTableProps {
  results: CountryResult[];
  selectedCountry: string | null;
  onCountrySelect: (iso: string) => void;
}

export function ResultsTable({ results, selectedCountry, onCountrySelect }: ResultsTableProps) {
  return (
    <div className="overflow-hidden rounded-2xl border border-slate-700/50">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="bg-slate-800/50 border-b border-slate-700/50">
              <th className="px-4 py-3 text-left text-xs text-muted-foreground uppercase tracking-wider">Rank</th>
              <th className="px-4 py-3 text-left text-xs text-muted-foreground uppercase tracking-wider">ISO</th>
              <th className="px-4 py-3 text-left text-xs text-muted-foreground uppercase tracking-wider">Country</th>
              <th className="px-4 py-3 text-left text-xs text-muted-foreground uppercase tracking-wider">TOPSIS Score</th>
              <th className="px-4 py-3 text-left text-xs text-muted-foreground uppercase tracking-wider">RC Score</th>
              <th className="px-4 py-3 text-left text-xs text-muted-foreground uppercase tracking-wider">GDP/Capita</th>
              <th className="px-4 py-3 text-left text-xs text-muted-foreground uppercase tracking-wider">Digital Infra</th>
              <th className="px-4 py-3 text-left text-xs text-muted-foreground uppercase tracking-wider">Job Market</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-700/30">
            {results.map((result) => (
              <tr
                key={result.iso}
                onClick={() => onCountrySelect(result.iso)}
                className={`
                  cursor-pointer transition-all duration-200
                  ${selectedCountry === result.iso 
                    ? 'bg-blue-500/10 border-l-4 border-l-blue-500' 
                    : 'hover:bg-slate-800/30'
                  }
                `}
              >
                <td className="px-4 py-4">
                  <div className="flex items-center gap-2">
                    <div className={`
                      w-6 h-6 rounded-full flex items-center justify-center text-xs
                      ${result.rank === 1 ? 'bg-yellow-500/20 text-yellow-400' :
                        result.rank === 2 ? 'bg-slate-400/20 text-slate-300' :
                        result.rank === 3 ? 'bg-orange-500/20 text-orange-400' :
                        'bg-slate-700/30 text-slate-400'}
                    `}>
                      {result.rank}
                    </div>
                  </div>
                </td>
                <td className="px-4 py-4 text-sm text-muted-foreground">{result.iso}</td>
                <td className="px-4 py-4 text-sm text-foreground">{result.country}</td>
                <td className="px-4 py-4">
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-emerald-400">{result.topsisScore.toFixed(3)}</span>
                    <div className="w-16 h-1.5 bg-slate-700/50 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-gradient-to-r from-emerald-500 to-blue-500 rounded-full"
                        style={{ width: `${result.topsisScore * 100}%` }}
                      />
                    </div>
                  </div>
                </td>
                <td className="px-4 py-4 text-sm text-slate-300">{result.rcScore.toFixed(2)}</td>
                <td className="px-4 py-4 text-sm text-slate-300">{result.gdpPerCapita.toLocaleString()}</td>
                <td className="px-4 py-4 text-sm text-slate-300">{result.digitalInfra.toFixed(2)}</td>
                <td className="px-4 py-4 text-sm text-slate-300">{result.jobMarket.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
