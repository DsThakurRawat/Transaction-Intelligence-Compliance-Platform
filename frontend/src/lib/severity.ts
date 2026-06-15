export const BAND = {
  critical: { solid: '#C2334D', soft: '#F7E0E4', label: 'Critical' },
  high:     { solid: '#D86A2C', soft: '#F8E6D9', label: 'High' },
  medium:   { solid: '#C29A2E', soft: '#F6EDD7', label: 'Medium' },
  low:      { solid: '#3E7CA8', soft: '#E1ECF4', label: 'Low' },
  clean:    { solid: '#2E8B6F', soft: '#DCEFE8', label: 'Clean' },
} as const;

export type RiskBand = keyof typeof BAND;
