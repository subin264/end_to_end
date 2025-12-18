import { useState } from 'react';
import { ScenarioTabs } from './ScenarioTabs';
import { ResultsTable } from './ResultsTable';
import { CountryDetailCard } from './CountryDetailCard';
import { ArrowLeft } from 'lucide-react';

interface CountryResult {
  rank: number;
  iso: string;
  country: string;
  topsisScore: number;
  rcScore: number;
  gdpPerCapita: number;
  digitalInfra: number;
  jobMarket: number;
  description: string;
}

// Sample data for different scenarios
const scenarioData: Record<string, CountryResult[]> = {
  'balanced': [
    { rank: 1, iso: 'USA', country: 'United States', topsisScore: 0.892, rcScore: 72.5, gdpPerCapita: 69287, digitalInfra: 88.3, jobMarket: 91.2, description: 'The United States leads with balanced excellence across all metrics. Strong job market and digital infrastructure make it ideal for AI startups seeking talent and technical capabilities.' },
    { rank: 2, iso: 'GBR', country: 'United Kingdom', topsisScore: 0.845, rcScore: 68.2, gdpPerCapita: 46125, digitalInfra: 85.7, jobMarket: 84.6, description: 'The UK offers a strong regulatory environment and competitive job market, particularly in London. Good balance between market access and talent availability.' },
    { rank: 3, iso: 'CAN', country: 'Canada', topsisScore: 0.821, rcScore: 75.8, gdpPerCapita: 52051, digitalInfra: 83.4, jobMarket: 79.5, description: 'Canada provides favorable regulations and a welcoming environment for tech companies. Strong immigration policies support talent acquisition.' },
    { rank: 4, iso: 'AUS', country: 'Australia', topsisScore: 0.798, rcScore: 71.3, gdpPerCapita: 51812, digitalInfra: 82.1, jobMarket: 76.8, description: 'Australia combines strong digital infrastructure with a stable regulatory framework. Growing tech ecosystem in Sydney and Melbourne.' },
    { rank: 5, iso: 'DEU', country: 'Germany', topsisScore: 0.776, rcScore: 65.4, gdpPerCapita: 50795, digitalInfra: 81.9, jobMarket: 82.3, description: 'Germany offers access to the EU market with strong engineering talent. Regulations favor data privacy and consumer protection.' },
    { rank: 6, iso: 'KOR', country: 'South Korea', topsisScore: 0.754, rcScore: 69.7, gdpPerCapita: 35196, digitalInfra: 92.5, jobMarket: 74.2, description: 'South Korea leads in digital infrastructure with world-class connectivity. Strong government support for AI and technology sectors.' }
  ],
  'talent-focused': [
    { rank: 1, iso: 'USA', country: 'United States', topsisScore: 0.921, rcScore: 72.5, gdpPerCapita: 69287, digitalInfra: 88.3, jobMarket: 91.2, description: 'The United States dominates in AI talent with deep pools in Silicon Valley, Boston, and Seattle. Top universities and competitive compensation attract global talent.' },
    { rank: 2, iso: 'GBR', country: 'United Kingdom', topsisScore: 0.867, rcScore: 68.2, gdpPerCapita: 46125, digitalInfra: 85.7, jobMarket: 84.6, description: 'The UK, particularly London, offers strong AI research talent from leading universities like Oxford and Cambridge.' },
    { rank: 3, iso: 'DEU', country: 'Germany', topsisScore: 0.834, rcScore: 65.4, gdpPerCapita: 50795, digitalInfra: 81.9, jobMarket: 82.3, description: 'Germany provides excellent engineering talent with strong technical education and research institutions.' },
    { rank: 4, iso: 'CAN', country: 'Canada', topsisScore: 0.812, rcScore: 75.8, gdpPerCapita: 52051, digitalInfra: 83.4, jobMarket: 79.5, description: 'Canada has emerged as an AI research hub with centers in Toronto, Montreal, and Vancouver. Immigration-friendly policies attract talent.' },
    { rank: 5, iso: 'AUS', country: 'Australia', topsisScore: 0.781, rcScore: 71.3, gdpPerCapita: 51812, digitalInfra: 82.1, jobMarket: 76.8, description: 'Australia offers growing AI talent pools and quality of life that attracts international workers.' },
    { rank: 6, iso: 'KOR', country: 'South Korea', topsisScore: 0.765, rcScore: 69.7, gdpPerCapita: 35196, digitalInfra: 92.5, jobMarket: 74.2, description: 'South Korea has strong technical talent in AI and robotics, supported by major tech companies.' }
  ],
  'regulation-focused': [
    { rank: 1, iso: 'CAN', country: 'Canada', topsisScore: 0.887, rcScore: 75.8, gdpPerCapita: 52051, digitalInfra: 83.4, jobMarket: 79.5, description: 'Canada leads in regulatory clarity with progressive AI governance frameworks and supportive government policies.' },
    { rank: 2, iso: 'USA', country: 'United States', topsisScore: 0.856, rcScore: 72.5, gdpPerCapita: 69287, digitalInfra: 88.3, jobMarket: 91.2, description: 'The US offers relatively favorable regulations with innovation-friendly policies at federal and state levels.' },
    { rank: 3, iso: 'AUS', country: 'Australia', topsisScore: 0.829, rcScore: 71.3, gdpPerCapita: 51812, digitalInfra: 82.1, jobMarket: 76.8, description: 'Australia provides clear regulatory frameworks with balanced approach to innovation and consumer protection.' },
    { rank: 4, iso: 'KOR', country: 'South Korea', topsisScore: 0.801, rcScore: 69.7, gdpPerCapita: 35196, digitalInfra: 92.5, jobMarket: 74.2, description: 'South Korea maintains tech-friendly regulations with strong government support for AI development.' },
    { rank: 5, iso: 'GBR', country: 'United Kingdom', topsisScore: 0.778, rcScore: 68.2, gdpPerCapita: 46125, digitalInfra: 85.7, jobMarket: 84.6, description: 'The UK offers post-Brexit regulatory flexibility while maintaining high standards for AI governance.' },
    { rank: 6, iso: 'DEU', country: 'Germany', topsisScore: 0.743, rcScore: 65.4, gdpPerCapita: 50795, digitalInfra: 81.9, jobMarket: 82.3, description: 'Germany follows strict EU regulations with emphasis on data protection and ethical AI deployment.' }
  ],
  'market-focused': [
    { rank: 1, iso: 'USA', country: 'United States', topsisScore: 0.905, rcScore: 72.5, gdpPerCapita: 69287, digitalInfra: 88.3, jobMarket: 91.2, description: 'The United States offers the largest market with highest GDP per capita and consumer spending power.' },
    { rank: 2, iso: 'CAN', country: 'Canada', topsisScore: 0.871, rcScore: 75.8, gdpPerCapita: 52051, digitalInfra: 83.4, jobMarket: 79.5, description: 'Canada provides strong purchasing power and serves as gateway to North American markets.' },
    { rank: 3, iso: 'AUS', country: 'Australia', topsisScore: 0.847, rcScore: 71.3, gdpPerCapita: 51812, digitalInfra: 82.1, jobMarket: 76.8, description: 'Australia offers high GDP per capita with strong consumer markets in urban centers.' },
    { rank: 4, iso: 'DEU', country: 'Germany', topsisScore: 0.823, rcScore: 65.4, gdpPerCapita: 50795, digitalInfra: 81.9, jobMarket: 82.3, description: 'Germany provides access to wealthy European markets as the economic engine of the EU.' },
    { rank: 5, iso: 'GBR', country: 'United Kingdom', topsisScore: 0.798, rcScore: 68.2, gdpPerCapita: 46125, digitalInfra: 85.7, jobMarket: 84.6, description: 'The UK offers strong domestic market and serves as financial hub with high-value sectors.' },
    { rank: 6, iso: 'KOR', country: 'South Korea', topsisScore: 0.721, rcScore: 69.7, gdpPerCapita: 35196, digitalInfra: 92.5, jobMarket: 74.2, description: 'South Korea has growing market with tech-savvy consumers but lower GDP per capita.' }
  ],
  'infra-focused': [
    { rank: 1, iso: 'KOR', country: 'South Korea', topsisScore: 0.934, rcScore: 69.7, gdpPerCapita: 35196, digitalInfra: 92.5, jobMarket: 74.2, description: 'South Korea leads globally in digital infrastructure with fastest internet speeds and comprehensive 5G coverage.' },
    { rank: 2, iso: 'USA', country: 'United States', topsisScore: 0.891, rcScore: 72.5, gdpPerCapita: 69287, digitalInfra: 88.3, jobMarket: 91.2, description: 'The US provides world-class cloud infrastructure with major data centers and tech infrastructure.' },
    { rank: 3, iso: 'GBR', country: 'United Kingdom', topsisScore: 0.862, rcScore: 68.2, gdpPerCapita: 46125, digitalInfra: 85.7, jobMarket: 84.6, description: 'The UK offers strong digital connectivity and well-developed tech infrastructure in major cities.' },
    { rank: 4, iso: 'CAN', country: 'Canada', topsisScore: 0.839, rcScore: 75.8, gdpPerCapita: 52051, digitalInfra: 83.4, jobMarket: 79.5, description: 'Canada maintains excellent digital infrastructure with reliable connectivity across urban centers.' },
    { rank: 5, iso: 'AUS', country: 'Australia', topsisScore: 0.817, rcScore: 71.3, gdpPerCapita: 51812, digitalInfra: 82.1, jobMarket: 76.8, description: 'Australia has invested heavily in digital infrastructure despite geographic challenges.' },
    { rank: 6, iso: 'DEU', country: 'Germany', topsisScore: 0.795, rcScore: 65.4, gdpPerCapita: 50795, digitalInfra: 81.9, jobMarket: 82.3, description: 'Germany offers solid infrastructure though lags behind leaders in certain connectivity metrics.' }
  ]
};

const scenarioWeights: Record<string, { rc: number; gdp: number; infra: number; job: number }> = {
  'balanced': { rc: 0.25, gdp: 0.25, infra: 0.25, job: 0.25 },
  'talent-focused': { rc: 0.20, gdp: 0.20, infra: 0.20, job: 0.40 },
  'regulation-focused': { rc: 0.40, gdp: 0.20, infra: 0.20, job: 0.20 },
  'market-focused': { rc: 0.20, gdp: 0.40, infra: 0.20, job: 0.20 },
  'infra-focused': { rc: 0.20, gdp: 0.20, infra: 0.40, job: 0.20 }
};

interface ResultsScreenProps {
  onBack: () => void;
}

export function ResultsScreen({ onBack }: ResultsScreenProps) {
  const [selectedScenario, setSelectedScenario] = useState('talent-focused');
  const [selectedCountry, setSelectedCountry] = useState<string | null>('USA');

  const currentResults = scenarioData[selectedScenario];
  const currentWeights = scenarioWeights[selectedScenario];
  const selectedCountryDetail = currentResults.find(c => c.iso === selectedCountry) || null;

  return (
    <div className="dark min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 text-foreground p-8">
      <div className="max-w-[1800px] mx-auto">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={onBack}
            className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors mb-4"
          >
            <ArrowLeft className="w-4 h-4" />
            <span className="text-sm">Back to Configuration</span>
          </button>
          
          <h1 className="text-3xl mb-2 bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
            Global Entry Decision Support
          </h1>
          <p className="text-muted-foreground">
            Analysis Results & Country Comparison
          </p>
        </div>

        {/* Scenario Tabs */}
        <div className="mb-6">
          <ScenarioTabs
            selectedScenario={selectedScenario}
            onScenarioChange={setSelectedScenario}
          />
        </div>

        {/* Scenario Info */}
        <div className="bg-slate-900/50 backdrop-blur-sm rounded-2xl p-6 border border-slate-800/50 shadow-xl mb-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-muted-foreground mb-1">Active Scenario</div>
              <div className="text-xl text-foreground capitalize">
                {selectedScenario.replace('-', ' ')}
              </div>
            </div>
            <div className="flex items-center gap-6">
              <div className="text-sm">
                <span className="text-muted-foreground">Weights:</span>
                <span className="ml-2 text-blue-400">RC {currentWeights.rc.toFixed(2)}</span>
                <span className="mx-1 text-slate-600">•</span>
                <span className="text-purple-400">GDP {currentWeights.gdp.toFixed(2)}</span>
                <span className="mx-1 text-slate-600">•</span>
                <span className="text-emerald-400">Infra {currentWeights.infra.toFixed(2)}</span>
                <span className="mx-1 text-slate-600">•</span>
                <span className="text-amber-400">Job {currentWeights.job.toFixed(2)}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="grid grid-cols-3 gap-6">
          {/* Results Table - Takes 2 columns */}
          <div className="col-span-2 bg-slate-900/50 backdrop-blur-sm rounded-3xl p-8 border border-slate-800/50 shadow-2xl">
            <h2 className="text-muted-foreground uppercase tracking-wider text-sm mb-6">
              Country Rankings
            </h2>
            <ResultsTable
              results={currentResults}
              selectedCountry={selectedCountry}
              onCountrySelect={setSelectedCountry}
            />
          </div>

          {/* Country Detail Card - Takes 1 column */}
          <div className="col-span-1">
            <CountryDetailCard countryDetail={selectedCountryDetail} />
          </div>
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
