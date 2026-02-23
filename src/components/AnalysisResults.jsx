import React, { useRef, useEffect } from 'react';

const getColorForScore = (score) => {
  if (score <= 3) return '#16a34a'; // green
  if (score <= 6) return '#eab308'; // yellow
  return '#dc2626'; // red
};

const SemiCircleGauge = ({ score }) => {
  const normalized = Math.max(1, Math.min(10, score));
  const percent = (normalized - 1) / 9; // 0..1
  const stroke = 14;
  const radius = 60;
  const circumference = Math.PI * radius;
  const dash = percent * circumference;
  const gap = circumference - dash;
  const color = getColorForScore(score);

  // Use a larger viewBox so the semicircle and labels don't get clipped
  return (
    <svg width="200" height="140" viewBox="0 0 180 150" className="mx-auto" preserveAspectRatio="xMidYMid meet">
      <g transform="translate(90,90)">
        <path d={`M -${radius} 0 A ${radius} ${radius} 0 0 1 ${radius} 0`} fill="none" stroke="#e6e7eb" strokeWidth={stroke} strokeLinecap="round" />
        <path
          d={`M -${radius} 0 A ${radius} ${radius} 0 0 1 ${radius} 0`}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={`${dash} ${gap}`}
        />
        <text x="0" y="-20" textAnchor="middle" className="text-sm font-medium" fill="#111827" style={{fontSize: '14px'}}>
          Score
        </text>
        <text x="0" y="28" textAnchor="middle" className="font-bold" style={{fontSize: '20px', fill: color}}>
          {score}/10
        </text>
      </g>
    </svg>
  );
};

const AnalysisResults = ({ result }) => {
  const wrapperRef = useRef(null);

  useEffect(() => {
    if (wrapperRef.current) {
      wrapperRef.current.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }, []);

  if (!result) return null;
  const { score, verdict, red_flags, recommendation } = result;

  return (
    <div ref={wrapperRef} className="w-full max-w-2xl mx-auto bg-white rounded-lg shadow-lg p-6 mt-6">
      <div className="flex flex-col md:flex-row items-center md:items-start gap-6">
        <div className="flex-0 w-full md:w-1/3 flex justify-center">
          <SemiCircleGauge score={score} />
        </div>
        <div className="flex-1">
          <h2 className="text-2xl font-semibold text-slate-900">{verdict}</h2>
          <p className="text-sm text-slate-500 mt-1">Phishing assessment based on AI analysis</p>

          <div className="mt-4">
            <h3 className="text-lg font-medium text-slate-800">Reasoning Report</h3>
            <ul className="mt-2 space-y-2">
              {red_flags && red_flags.map((flag, i) => (
                <li key={i} className="p-3 bg-red-50 border border-red-100 rounded-md text-sm text-red-800">
                  {flag}
                </li>
              ))}
            </ul>
          </div>

          <div className="mt-4 p-4 bg-slate-50 border border-slate-100 rounded-md">
            <h4 className="font-semibold text-slate-800">Recommendation</h4>
            <p className="mt-2 text-sm text-slate-700">{recommendation}</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnalysisResults;
