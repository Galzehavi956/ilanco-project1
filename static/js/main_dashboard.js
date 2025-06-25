// 🟡 משתנה גלובלי לשמירה על גרפים פעילים
let existingCharts = {};

document.addEventListener('DOMContentLoaded', function () {
  // 🔹 תרשים עוגה – בקרת איכות
  const qualityLabels = window.qualityLabels;
  const qualityValues = window.qualityValues;

  const qualityCanvas = document.getElementById("qualityPie");
  if (existingCharts.qualityPie) {
    existingCharts.qualityPie.destroy();
  }
  existingCharts.qualityPie = new Chart(qualityCanvas, {
    type: 'pie',
    data: {
      labels: qualityLabels,
      datasets: [{
        data: qualityValues,
        backgroundColor: [ '#198754','#dc3545', '#ffc107', '#0dcaf0' ]
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { position: 'bottom' },
        tooltip: {
          callbacks: {
            label: function (context) {
              const label = context.label || '';
              const value = context.parsed;
              const total = context.chart._metasets[0].total;
              const percentage = ((value / total) * 100).toFixed(1);
              return `${label}: ${value} (${percentage}%)`;
            }
          }
        },
        datalabels: {
          color: '#000',
          font: { weight: 'bold' },
          formatter: (value, context) => {
            const total = context.chart.data.datasets[0].data.reduce((a, b) => a + b, 0);
            const percentage = ((value / total) * 100).toFixed(1);
            return `${percentage}%`;
          }
        }
      }
    },
    plugins: [ChartDataLabels]
  });

  // 🔹 תרשים עמודות – ייצור לפי תאריכים (מעוצב)
  const barLabels = window.barLabels;
  const barValues = window.barValues;

  const barCanvas = document.getElementById("productionBar");
  if (existingCharts.productionBar) {
    existingCharts.productionBar.destroy();
  }
  existingCharts.productionBar = new Chart(barCanvas, {
    type: 'bar',
    data: {
      labels: barLabels,
      datasets: [{
        label: 'תוכניות ייצור',
        data: barValues,
        backgroundColor: 'rgba(0, 123, 255, 0.6)',         // צבע אלגנטי
        borderColor: 'rgba(0, 123, 255, 1)',
        borderWidth: 1,
        borderRadius: 10,
        barThickness: 36
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      layout: {
        padding: {
          top: 20,
          bottom: 10
        }
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#fff',
          titleColor: '#000',
          bodyColor: '#000',
          borderColor: '#ccc',
          borderWidth: 1,
          callbacks: {
            label: function (context) {
              return `כמות: ${context.parsed.y}`;
            }
          }
        },
        datalabels: {
          anchor: 'end',
          align: 'top',
          color: '#111',
          font: {
            weight: 'bold',
            size: 13
          },
          padding: {
            top: 4
          },
          formatter: (value) => value
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          suggestedMax: Math.max(...barValues) + 1,   // מרווח אוטומטי למעלה
          title: {
            display: true,
            text: 'מספר תוכניות',
            color: '#333',
            font: { size: 13 }
          },
          ticks: {
            color: '#444',
            stepSize: 1
          },
          grid: {
            color: 'rgba(0, 0, 0, 0.04)'
          }
        },
        x: {
          ticks: {
            color: '#444',
            font: {
              size: 12
            }
          },
          grid: {
            display: false
          }
        }
      }
    },
    plugins: [ChartDataLabels]
  });

  // 🔸 תרשים עוגה – התפלגות עדיפות
  fetch('/api/production/priority-distribution')
    .then(response => response.json())
    .then(data => {
      const ctx = document.getElementById('priorityPieChart').getContext('2d');

      if (existingCharts.priorityPieChart) {
        existingCharts.priorityPieChart.destroy();
      }

      existingCharts.priorityPieChart = new Chart(ctx, {
        type: 'pie',
        data: {
          labels: Object.keys(data),
          datasets: [{
            label: 'עדיפות',
            data: Object.values(data),
            backgroundColor: ['#ffc107', '#dc3545', '#28a745']
          }]
        },
        options: {
          responsive: true,
          plugins: {
            legend: { position: 'bottom' },
            tooltip: {
              callbacks: {
                label: function (context) {
                  const label = context.label || '';
                  const value = context.parsed;
                  const total = context.chart._metasets[0].total;
                  const percentage = ((value / total) * 100).toFixed(1);
                  return `${label}: ${value} (${percentage}%)`;
                }
              }
            },
            datalabels: {
              color: '#000',
              font: { weight: 'bold' },
              formatter: (value, context) => {
                const total = context.chart.data.datasets[0].data.reduce((a, b) => a + b, 0);
                const percentage = ((value / total) * 100).toFixed(1);
                return `${percentage}%`;
              }
            }
          }
        },
        plugins: [ChartDataLabels]
      });
    });

  // 🔽 כפתור ייצוא PDF לגרף עמודות
  const exportBtn = document.getElementById("exportBarChartPDF");
  if (exportBtn) {
    exportBtn.addEventListener("click", async function () {
      const { jsPDF } = window.jspdf;
      const chartCanvas = document.getElementById("productionBar");
      const chartImage = chartCanvas.toDataURL("image/png");

      const pdf = new jsPDF({
        orientation: "landscape",
        unit: "px",
        format: [chartCanvas.width, chartCanvas.height]
      });

      pdf.addImage(chartImage, 'PNG', 0, 0, chartCanvas.width, chartCanvas.height);
      pdf.save("production_chart.pdf");
    });
  }
});