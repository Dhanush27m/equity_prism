/**
 * Component: Frontend -> components -> Candlestick price chart
 * Belongs to: rendered on the Company page from GET /api/companies/{symbol}/history data.
 * Purpose: wraps TradingView's lightweight-charts library (a purpose-built financial
 * charting library, chosen over the general-purpose Recharts used elsewhere for exactly
 * this OHLCV use case) into a candlestick + volume chart that re-themes with light/dark mode.
 */

"use client";

import {
  ColorType,
  CrosshairMode,
  createChart,
  type IChartApi,
} from "lightweight-charts";
import * as React from "react";

import { useTheme } from "@/components/providers";
import type { Candle } from "@/lib/types";

export function PriceChart({ candles }: { candles: Candle[] }) {
  const ref = React.useRef<HTMLDivElement>(null);
  const chartRef = React.useRef<IChartApi | null>(null);
  const { theme } = useTheme();

  // Rebuilds the chart whenever candles or the theme changes (lightweight-charts isn't
  // designed for partial re-theming, so the whole chart is torn down and recreated).
  React.useEffect(() => {
    if (!ref.current) return;
    const dark = theme === "dark";
    const grid = dark ? "#1a2230" : "#eef1f5";
    const text = dark ? "#8b98a9" : "#5b6673";

    const chart = createChart(ref.current, {
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: text,
        fontSize: 11,
      },
      grid: { vertLines: { color: grid }, horzLines: { color: grid } },
      crosshair: { mode: CrosshairMode.Normal },
      rightPriceScale: { borderColor: grid },
      timeScale: { borderColor: grid, timeVisible: false },
      height: 380,
      autoSize: true,
    });
    chartRef.current = chart;

    const candleSeries = chart.addCandlestickSeries({
      upColor: "#16a34a",
      downColor: "#dc2626",
      borderUpColor: "#16a34a",
      borderDownColor: "#dc2626",
      wickUpColor: "#16a34a",
      wickDownColor: "#dc2626",
    });
    candleSeries.setData(
      candles.map((c) => ({
        time: c.time,
        open: c.open,
        high: c.high,
        low: c.low,
        close: c.close,
      }))
    );

    // Volume histogram on a separate price scale pinned to the bottom ~18% of the
    // chart, colored per-candle to match the candlestick's up/down color.
    const volSeries = chart.addHistogramSeries({
      priceFormat: { type: "volume" },
      priceScaleId: "vol",
    });
    volSeries.priceScale().applyOptions({
      scaleMargins: { top: 0.82, bottom: 0 },
    });
    volSeries.setData(
      candles.map((c) => ({
        time: c.time,
        value: c.volume,
        color: c.close >= c.open ? "rgba(22,163,74,0.4)" : "rgba(220,38,38,0.4)",
      }))
    );

    chart.timeScale().fitContent();

    return () => {
      chart.remove();
      chartRef.current = null;
    };
  }, [candles, theme]);

  return <div ref={ref} className="w-full" />;
}
