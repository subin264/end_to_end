import { Slider } from './ui/slider';

interface Weight {
  id: string;
  label: string;
  technicalLabel: string;
  value: number;
}

interface WeightAdjusterProps {
  weights: Weight[];
  onWeightChange: (id: string, value: number) => void;
}

export function WeightAdjuster({ weights, onWeightChange }: WeightAdjusterProps) {
  return (
    <div className="flex flex-col gap-6">
      <h2 className="text-muted-foreground uppercase tracking-wider text-sm">
        Adjust Weights
      </h2>
      
      <div className="flex flex-col gap-8">
        {weights.map((weight) => (
          <div key={weight.id} className="flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <div className="flex flex-col gap-0.5">
                <span className="text-foreground/90">
                  {weight.label}
                </span>
                <span className="text-xs text-muted-foreground">
                  {weight.technicalLabel}
                </span>
              </div>
              <div className="px-3 py-1 rounded-lg bg-blue-500/10 border border-blue-500/30 text-blue-400 text-sm min-w-[60px] text-center">
                {weight.value}%
              </div>
            </div>
            
            <Slider
              value={[weight.value]}
              onValueChange={(values) => onWeightChange(weight.id, values[0])}
              min={0}
              max={100}
              step={1}
              className="w-full"
            />
          </div>
        ))}
      </div>
    </div>
  );
}
