import { useState } from 'react';

interface Strategy {
  id: string;
  title: string;
  subtitle: string;
}

const strategies: Strategy[] = [
  {
    id: 'balanced',
    title: 'Balanced',
    subtitle: 'Equal consideration across all factors'
  },
  {
    id: 'talent-focused',
    title: 'Talent-Focused',
    subtitle: 'For AI startups that care about hiring'
  },
  {
    id: 'regulation-focused',
    title: 'Regulation-Focused',
    subtitle: 'Prioritize favorable regulatory environments'
  },
  {
    id: 'market-focused',
    title: 'Market-Focused',
    subtitle: 'Emphasize market size and economic potential'
  },
  {
    id: 'infra-focused',
    title: 'Infra-Focused',
    subtitle: 'Optimize for digital infrastructure quality'
  }
];

interface StrategySelectorProps {
  selectedStrategy: string;
  onStrategyChange: (strategyId: string) => void;
}

export function StrategySelector({ selectedStrategy, onStrategyChange }: StrategySelectorProps) {
  return (
    <div className="flex flex-col gap-6">
      <h2 className="text-muted-foreground uppercase tracking-wider text-sm">
        Choose a Strategy
      </h2>
      
      <div className="flex flex-col gap-3">
        {strategies.map((strategy) => (
          <button
            key={strategy.id}
            onClick={() => onStrategyChange(strategy.id)}
            className={`
              relative px-6 py-4 rounded-2xl text-left transition-all duration-300
              border border-border/50
              ${
                selectedStrategy === strategy.id
                  ? 'bg-gradient-to-br from-blue-500/20 to-purple-500/20 border-blue-500/50 shadow-lg shadow-blue-500/10'
                  : 'bg-card/50 hover:bg-card/80 hover:border-border'
              }
            `}
          >
            <div className="flex flex-col gap-1">
              <div className={`${selectedStrategy === strategy.id ? 'text-foreground' : 'text-foreground/90'}`}>
                {strategy.title}
              </div>
              <div className="text-xs text-muted-foreground">
                {strategy.subtitle}
              </div>
            </div>
            
            {selectedStrategy === strategy.id && (
              <div className="absolute top-4 right-4 w-2 h-2 rounded-full bg-blue-400 shadow-lg shadow-blue-400/50" />
            )}
          </button>
        ))}
      </div>
    </div>
  );
}
