import React from 'react';
import { Card, CardContent } from './ui/card';

interface ScoreMeterProps {
  score?: number;
  label: string;
  size?: 'sm' | 'md' | 'lg';
}

const ScoreMeter: React.FC<ScoreMeterProps> = ({ score, label, size = 'md' }) => {
  if (score === undefined || score === null) {
    return (
      <Card className="bg-muted/50">
        <CardContent className={`p-4 text-center ${size === 'sm' ? 'p-2' : ''}`}>
          <div className="text-muted-foreground">Not analyzed</div>
          <div className="text-xs text-muted-foreground mt-1">{label}</div>
        </CardContent>
      </Card>
    );
  }

  const getColor = (score: number) => {
    if (score >= 80) return 'bg-green-500';
    if (score >= 60) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const getSizeClasses = (size: string) => {
    switch (size) {
      case 'sm': return 'p-2';
      case 'lg': return 'p-6';
      default: return 'p-4';
    }
  };

  const getTextSize = (size: string) => {
    switch (size) {
      case 'sm': return 'text-lg';
      case 'lg': return 'text-3xl';
      default: return 'text-2xl';
    }
  };

  return (
    <Card className="bg-muted/50">
      <CardContent className={`text-center ${getSizeClasses(size)}`}>
        <div className={`font-bold ${getTextSize(size)} ${getColor(score)}`}>
          {score}
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
          <div
            className={`h-2 rounded-full ${getColor(score)} transition-all duration-500`}
            style={{ width: `${score}%` }}
          />
        </div>
        <div className="text-xs text-muted-foreground mt-1">{label}</div>
      </CardContent>
    </Card>
  );
};

export default ScoreMeter;