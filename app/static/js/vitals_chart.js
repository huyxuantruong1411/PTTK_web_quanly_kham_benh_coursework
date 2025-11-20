document.addEventListener("DOMContentLoaded", function () {
    const vitalsDataEl = document.getElementById('vitals-data');
    const vitalsData = JSON.parse(vitalsDataEl.textContent);

    const ctx = document.getElementById('vitalsChart').getContext('2d');
    const vitalsChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: vitalsData.dates,
            datasets: [
                {
                    label: 'Nhịp Tim',
                    data: vitalsData.nhiptim,
                    borderColor: 'red',
                    fill: false
                },
                {
                    label: 'Cân Nặng',
                    data: vitalsData.cannang,
                    borderColor: 'blue',
                    fill: false
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: true
                },
                title: {
                    display: true,
                    text: 'Tiến triển chỉ số sinh tồn'
                }
            },
            scales: {
                y: {
                    beginAtZero: false
                }
            }
        }
    });
});
