import { useState } from 'react';
import { StrategySelector } from './components/StrategySelector';
import { WeightAdjuster } from './components/WeightAdjuster';
import { ResultsScreen } from './components/ResultsScreen';
import { Play } from 'lucide-react';

interface Weight {
  id: string;
  label: string;
  technicalLabel: string;
  value: number;
}

export default function App() {
  const [showResults, setShowResults] = useState(false);
  const [selectedStrategy, setSelectedStrategy] = useState('balanced');
  const [weights, setWeights] = useState<Weight[]>([
    {
      id: 'regulation',
      label: 'Regulation Complexity',
      technicalLabel: 'RC_score',
      value: 25
    },
    {
      id: 'market',
      label: 'Market Size',
      technicalLabel: 'gdp_per_capita',
      value: 25
    },
    {
      id: 'infrastructure',
      label: 'Digital Infrastructure',
      technicalLabel: 'digital_infra_index',
      value: 25
    },
    {
      id: 'talent',
      label: 'AI Job Market',
      technicalLabel: 'ai_job_market_score',
      value: 25
    }
  ]);

  const handleWeightChange = (id: string, value: number) => {
    setWeights(weights.map(w => 
      w.id === id ? { ...w, value } : w
    ));
  };

  const handleRunAnalysis = () => {
    console.log('Running analysis with strategy:', selectedStrategy);
    console.log('Weights:', weights);
    setShowResults(true);
  };

  if (showResults) {
    return <ResultsScreen onBack={() => setShowResults(false)} />;
  }

  return (
    <div className="dark min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 text-foreground p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-12">
          <h1 className="text-3xl mb-2 bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
            Global Entry Decision Support
          </h1>
          <p className="text-muted-foreground">
            Configure your analysis parameters
          </p>
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-2 gap-12 mb-12">
          {/* Left Side - Strategy Selection */}
          <div className="bg-slate-900/50 backdrop-blur-sm rounded-3xl p-8 border border-slate-800/50 shadow-2xl">
            <StrategySelector
              selectedStrategy={selectedStrategy}
              onStrategyChange={setSelectedStrategy}
            />
          </div>

          {/* Right Side - Weight Adjustment */}
          <div className="bg-slate-900/50 backdrop-blur-sm rounded-3xl p-8 border border-slate-800/50 shadow-2xl">
            <WeightAdjuster
              weights={weights}
              onWeightChange={handleWeightChange}
            />
          </div>
        </div>

        {/* Bottom - Run Analysis Button */}
        <div className="flex justify-center">
          <button
            onClick={handleRunAnalysis}
            className="group relative px-12 py-4 rounded-2xl bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 transition-all duration-300 shadow-lg shadow-blue-500/25 hover:shadow-xl hover:shadow-blue-500/40 border border-blue-400/30"
          >
            <div className="flex items-center gap-3">
              <Play className="w-5 h-5" fill="currentColor" />
              <span>Run Analysis</span>
            </div>
          </button>
        </div>

        {/* Decorative Elements */}
        <div className="fixed top-0 left-0 w-full h-full pointer-events-none overflow-hidden -z-10">
          <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-500/5 rounded-full blur-3xl" />
          <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-500/5 rounded-full blur-3xl" />
        </div>
      </div>
    </div>
  );
}