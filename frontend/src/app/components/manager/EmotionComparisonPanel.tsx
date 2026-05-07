import { useState } from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer,
} from "recharts";
import { TrendingUp, AlertCircle } from "lucide-react";

export interface EmotionDistribution {
  emotion: string;
  count: number;
  pct: number;
}

export interface FusionQuality {
  acousticTextAgreementRate: number;
  fusedMatchesAcousticRate: number;
  fusedMatchesTextRate: number;
  disagreementCount: number;
}

export interface EmotionComparisonData {
  totalUtterances: number;
  distributions: {
    acoustic: EmotionDistribution[];
    text: EmotionDistribution[];
    fused: EmotionDistribution[];
  };
  quality: FusionQuality;
}

interface EmotionComparisonPanelProps {
  data: EmotionComparisonData;
}

const EMOTION_COLORS: Record<string, string> = {
  neutral: "#6B7280", happy: "#10B981", sad: "#8B5CF6",
  angry: "#EF4444", frustrated: "#F59E0B", empathetic: "#06B6D4",
  calm: "#3B82F6", disgust: "#EC4899", fear: "#F97316", surprise: "#FBBF24",
};

function getQualityIndicator(rate: number) {
  if (rate >= 80) return { color: "#10B981", label: "Excellent", icon: "✓" };
  if (rate >= 60) return { color: "#3B82F6", label: "Good", icon: "→" };
  if (rate >= 40) return { color: "#F59E0B", label: "Fair", icon: "⚠" };
  return { color: "#EF4444", label: "Poor", icon: "✗" };
}

function formatDistributionForChart(
  distributions: EmotionComparisonData["distributions"],
): Array<{ name: string; acoustic: number; text: number; fused: number }> {
  const emotionMap = new Map<string, { acoustic: number; text: number; fused: number }>();
  const allEmotions = new Set<string>();

  [...distributions.acoustic, ...distributions.text, ...distributions.fused].forEach((d) => {
    allEmotions.add(d.emotion);
  });

  allEmotions.forEach((emotion) => {
    emotionMap.set(emotion, {
      acoustic: distributions.acoustic.find((d) => d.emotion === emotion)?.count ?? 0,
      text: distributions.text.find((d) => d.emotion === emotion)?.count ?? 0,
      fused: distributions.fused.find((d) => d.emotion === emotion)?.count ?? 0,
    });
  });

  return Array.from(emotionMap.entries())
    .map(([emotion, counts]) => ({
      name: emotion.charAt(0).toUpperCase() + emotion.slice(1),
      ...counts,
    }))
    .sort((a, b) => b.acoustic + b.text + b.fused - (a.acoustic + a.text + a.fused))
    .slice(0, 6);
}

export function EmotionComparisonPanel({ data }: EmotionComparisonPanelProps) {
  const chartData = formatDistributionForChart(data.distributions);
  const acousticQuality = getQualityIndicator(data.quality.acousticTextAgreementRate);
  const fusedAcousticQuality = getQualityIndicator(data.quality.fusedMatchesAcousticRate);
  const fusedTextQuality = getQualityIndicator(data.quality.fusedMatchesTextRate);

  return (
    <div className="space-y-5">
      <div className="flex items-center gap-2">
        <div className="w-9 h-9 bg-primary/10 rounded-lg flex items-center justify-center">
          <TrendingUp className="w-4.5 h-4.5 text-primary" />
        </div>
        <div>
          <h3 className="text-sm font-semibold text-foreground">Emotion Intelligence</h3>
          <p className="text-xs text-muted-foreground">{data.totalUtterances} utterances analyzed</p>
        </div>
      </div>

      {/* Agreement rates */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {[
          { label: "Acoustic ↔ Text", quality: acousticQuality, value: data.quality.acousticTextAgreementRate, desc: "agreement" },
          { label: "Fused → Acoustic", quality: fusedAcousticQuality, value: data.quality.fusedMatchesAcousticRate, desc: "Fusion aligns with audio" },
          { label: "Fused → Text", quality: fusedTextQuality, value: data.quality.fusedMatchesTextRate, desc: "Fusion aligns with text" },
        ].map((item) => (
          <div key={item.label} className="bg-card rounded-lg border border-border p-4 hover:shadow-sm transition-shadow">
            <div className="flex items-start justify-between mb-2">
              <span className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">{item.label}</span>
              <div className="px-1.5 py-0.5 rounded text-[11px] font-semibold"
                style={{ backgroundColor: `color-mix(in srgb, ${item.quality.color} 12%, transparent)`, color: item.quality.color }}>
                {item.quality.icon}
              </div>
            </div>
            <div className="text-2xl font-bold text-foreground mb-0.5">{item.value.toFixed(1)}%</div>
            <p className="text-[11px] text-muted-foreground">{item.quality.label} {item.desc}</p>
          </div>
        ))}
      </div>

      {data.quality.disagreementCount > 0 && (
        <div className="rounded-lg p-3 flex items-start gap-2.5 bg-red-500/5 border-l-[3px] border-red-500">
          <AlertCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
          <div>
            <p className="text-[13px] font-semibold text-foreground">Cross-Modal Disagreement</p>
            <p className="text-[12px] text-muted-foreground mt-0.5">
              {data.quality.disagreementCount} utterance{data.quality.disagreementCount !== 1 ? "s" : ""} show mismatch between acoustic and text emotions.
            </p>
          </div>
        </div>
      )}

      {/* Bar chart */}
      <div className="bg-card rounded-lg border border-border p-5">
        <h4 className="text-[13px] font-semibold text-foreground mb-4">Emotion Distribution</h4>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={chartData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
            <XAxis dataKey="name" tick={{ fontSize: 11, fill: "var(--muted-foreground)" }} axisLine={{ stroke: "var(--border)" }} />
            <YAxis tick={{ fontSize: 11, fill: "var(--muted-foreground)" }} axisLine={{ stroke: "var(--border)" }} />
            <Tooltip
              contentStyle={{
                backgroundColor: "var(--card)",
                border: "1px solid var(--border)",
                borderRadius: "8px",
                color: "var(--foreground)",
              }}
              labelStyle={{ color: "var(--foreground)" }}
              itemStyle={{ color: "var(--muted-foreground)" }}
            />
            <Legend wrapperStyle={{ paddingTop: "16px" }} />
            <Bar dataKey="acoustic" name="Acoustic (Audio)" fill="#3B82F6" radius={[2, 2, 0, 0]} />
            <Bar dataKey="text" name="Text (NLP)" fill="#10B981" radius={[2, 2, 0, 0]} />
            <Bar dataKey="fused" name="Fused (Composite)" fill="#8B5CF6" radius={[2, 2, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Distribution breakdowns */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {([
          { title: "Acoustic Emotions", items: data.distributions.acoustic, prefix: "ac" },
          { title: "Text Emotions", items: data.distributions.text, prefix: "tx" },
          { title: "Fused Emotions", items: data.distributions.fused, prefix: "fu" },
        ] as const).map((section) => (
          <div key={section.prefix} className="bg-card rounded-lg border border-border p-4">
            <h5 className="text-[11px] font-semibold uppercase text-muted-foreground mb-2.5">{section.title}</h5>
            <div className="space-y-1.5">
              {section.items.slice(0, 4).map((item) => (
                <div key={`${section.prefix}-${item.emotion}`} className="flex items-center justify-between text-[12px]">
                  <div className="flex items-center gap-2 flex-1">
                    <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: EMOTION_COLORS[item.emotion] || "#9CA3AF" }} />
                    <span className="text-foreground font-medium capitalize">{item.emotion}</span>
                  </div>
                  <span className="text-muted-foreground">{item.count} ({item.pct.toFixed(1)}%)</span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
