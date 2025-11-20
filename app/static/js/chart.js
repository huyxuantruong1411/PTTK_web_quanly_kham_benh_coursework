// charts.js – external Chart.js initializer for Flask templates

// The HTML template must define:
// window.chartData = {
//     dates: [...],
//     appointmentCounts: [...],
//     medicineLabels: [...],
//     medicineData: [...],
//     revenueLabels: [...],
//     revenueData: [...]
// };

// -----------------------------
// Generic chart creator helpers
// -----------------------------

function createBarChart(ctxId, labels, data, label) {
    const ctx = document.getElementById(ctxId);
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: label,
                data: data,
                borderWidth: 1
            }]
        },
        options: {
            scales: {
                y: { beginAtZero: true }
            }
        }
    });
}

function createLineChart(ctxId, labels, data, label) {
    const ctx = document.getElementById(ctxId);
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: label,
                data: data,
                fill: false,
                borderWidth: 2
            }]
        },
        options: {
            scales: {
                y: { beginAtZero: true }
            }
        }
    });
}

// -----------------------------
// Initialize charts after load
// -----------------------------

window.addEventListener('DOMContentLoaded', function () {
    if (!window.chartData) {
        console.error('chartData is not defined. Make sure to inject data in HTML before this file loads.');
        return;
    }

    // Appointment chart
    createBarChart(
        'appointmentChart',
        window.chartData.dates,
        window.chartData.appointmentCounts,
        'Số lượng lịch hẹn theo ngày'
    );

    // Top medicines chart
    createBarChart(
        'medicineChart',
        window.chartData.medicineLabels,
        window.chartData.medicineData,
        'Top 5 Thuốc được kê nhiều nhất'
    );

    // Revenue chart
    createLineChart(
        'revenueChart',
        window.chartData.revenueLabels,
        window.chartData.revenueData,
        'Doanh thu theo ngày'
    );
});
