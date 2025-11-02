import { useMemo } from "react";
import {
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Legend,
  LinearScale,
  Title,
  Tooltip,
} from "chart.js";
import { Bar } from "react-chartjs-2";

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

export default function MandayChart({ chart }) {
  const data = useMemo(
    () => ({
      labels: chart?.labels ?? [],
      datasets: [
        {
          label: "Manday",
          data: chart?.values ?? [],
          backgroundColor: "#0d6efd",
          borderRadius: 4,
        },
      ],
    }),
    [chart],
  );

  const options = useMemo(
    () => ({
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: { beginAtZero: true, title: { display: true, text: "Manday" } },
      },
    }),
    [],
  );

  if (!chart || !chart.labels || chart.labels.length === 0) {
    return <p className="muted">Manday chart will populate once activities are added.</p>;
  }

  return (
    <div className="manday-chart">
      <Bar options={options} data={data} />
    </div>
  );
}
