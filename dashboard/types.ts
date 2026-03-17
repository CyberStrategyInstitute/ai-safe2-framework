
export type PillarType = 
  | "Sanitize & Isolate"
  | "Audit & Inventory" 
  | "Fail-Safe & Recovery"
  | "Engage & Monitor"
  | "Evolve & Educate";

export type RiskLevel = "Low" | "Medium" | "High" | "Critical";

export interface ControlComponent {
  title: string;
  desc: string;
}

export interface Control {
  id: string;
  name: string;
  pillar: PillarType;
  sub_topic: string;
  is_gap_filler: boolean;
  description: string;
  decision_maker_impact: string;
  implementation_guidance: string;
  related_frameworks: string[];
  risk_level: RiskLevel;
  // GRC Reconciliation Fields
  components?: ControlComponent[];
  cross_reference?: string;
  framework_note?: string;
}

export interface TaxonomyFilter {
  pillar: PillarType | "All";
  riskLevel: RiskLevel | "All";
  isGapFiller: boolean | null;
  searchQuery: string;
}
