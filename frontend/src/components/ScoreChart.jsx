import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

export default function ScoreChart({ data }) {
  if (!data || data.length === 0) {
    return <p className="muted">No TOEFL attempts yet. Complete a TOEFL task to see your score trend here.</p>;
  }

  const chartData = data.map((row, i) => ({
    attempt: i + 1,
    score: row.score_band,
    date: new Date(row.created_at).toLocaleDateString(),
    task: row.task_type,
  }));

  return (
    <ResponsiveContainer width="100%" height={260}>
      <LineChart data={chartData} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#2c3d5e" />
        <XAxis dataKey="attempt" stroke="#9db0c9" tick={{ fontSize: 12 }} />
        <YAxis domain={[1, 6]} allowDecimals={false} stroke="#9db0c9" tick={{ fontSize: 12 }} />
        <Tooltip
          contentStyle={{ background: "#1a2740", border: "1px solid #2c3d5e", borderRadius: 8, color: "#e6ecf5" }}
          formatter={(value) => [`${value} / 6`, "Score band"]}
          labelFormatter={(label, payload) => {
            const item = payload?.[0]?.payload;
            return item ? `Attempt ${label} · ${item.task} · ${item.date}` : `Attempt ${label}`;
          }}
        />
        <Line type="monotone" dataKey="score" stroke="#4f9dff" strokeWidth={2} dot={{ r: 4 }} />
      </LineChart>
    </ResponsiveContainer>
  );
}
