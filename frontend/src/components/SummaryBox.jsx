export default function SummaryBox({ summary }) {
  if (!summary) {
    return null;
  }
  const items = [
    { label: "Duration (months)", value: summary.durationMonths },
    { label: "Total Manday", value: summary.totalManday },
    { label: "Total Budget (THB)", value: summary.totalBudget?.toLocaleString(undefined, { maximumFractionDigits: 2 }) },
  ];

  return (
    <div className="summary-box">
      {items.map((item) => (
        <div key={item.label} className="summary-item">
          <span className="summary-label">{item.label}</span>
          <span className="summary-value">{item.value ?? "-"}</span>
        </div>
      ))}
    </div>
  );
}
