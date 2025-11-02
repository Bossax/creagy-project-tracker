import { useEffect, useRef } from "react";
import Gantt from "frappe-gantt";

export default function GanttChart({ data = [] }) {
  const containerRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current || !Array.isArray(data) || data.length === 0) {
      if (containerRef.current) {
        containerRef.current.innerHTML = "<p class='muted'>No data available.</p>";
      }
      return;
    }
    const element = containerRef.current;
    element.innerHTML = "";
    const chart = new Gantt(element, data, {
      view_mode: "Month",
      language: "en",
      custom_popup_html: (task) =>
        `<div class="gantt-tooltip"><strong>${task.name}</strong><div>${task.start} → ${task.end}</div></div>`,
    });

    return () => {
      if (chart) {
        element.innerHTML = "";
      }
    };
  }, [data]);

  return <div className="gantt-container" ref={containerRef} />;
}
