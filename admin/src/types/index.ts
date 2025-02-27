export interface DailyStats {
  date: string
  total_visits: number
  unique_visitors: number
  avg_duration: number
  bounce_rate: number
}

export interface VisitStats {
  total_visits: number
  unique_visitors: number
  avg_daily_visits: number
  bounce_rate: number
  daily_data: DailyStats[]
}

export interface ChartData {
  dates: string[]
  visits: number[]
  visitors: number[]
} 