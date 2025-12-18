interface ScenarioTabsProps {
  selectedScenario: string;
  onScenarioChange: (scenario: string) => void;
}

const scenarios = [
  { id: 'balanced', label: 'Balanced' },
  { id: 'talent-focused', label: 'Talent-Focused' },
  { id: 'regulation-focused', label: 'Regulation-Focused' },
  { id: 'market-focused', label: 'Market-Focused' },
  { id: 'infra-focused', label: 'Infra-Focused' }
];

export function ScenarioTabs({ selectedScenario, onScenarioChange }: ScenarioTabsProps) {
  return (
    <div className="flex items-center gap-2 bg-slate-900/50 backdrop-blur-sm rounded-2xl p-1.5 border border-slate-800/50">
      {scenarios.map((scenario) => (
        <button
          key={scenario.id}
          onClick={() => onScenarioChange(scenario.id)}
          className={`
            px-4 py-2 rounded-xl text-sm transition-all duration-300
            ${selectedScenario === scenario.id
              ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg'
              : 'text-muted-foreground hover:text-foreground hover:bg-slate-800/50'
            }
          `}
        >
          {scenario.label}
        </button>
      ))}
    </div>
  );
}
