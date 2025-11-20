// Read data from JSON script
const rawData = document.getElementById("dashboard-data").textContent;
const data = JSON.parse(rawData);

// Chart defaults
Chart.defaults.font.family = 'Nunito';
Chart.defaults.color = '#858796';

// Weekly chart
const ctx = document.getElementById('weeklyChart').getContext('2d');

new Chart(ctx, {
    type: 'bar',
    data: {
        labels: data.daily_labels,
        datasets: [{
            label: 'Lượt khám',
            data: data.daily_values,
            backgroundColor: 'rgba(54, 162, 235, 0.3)',
            borderColor: 'rgba(54, 162, 235, 1)',
            borderWidth: 1
        }]
    },
    options: {
        responsive: true,
        plugins: {
            legend: { display: false },
            title: {
                display: true,
                text: 'Thống kê lượt khám theo ngày'
            }
        },
        scales: {
            y: { beginAtZero: true }
        }
    }
});
