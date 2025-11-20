// ===== Load data from embedded JSON =====
const reportDataElement = document.getElementById("report-data");
const reportData = JSON.parse(reportDataElement.textContent);

// ===== Extract variables =====
const FROM_DATE = reportData.from_date;
const TO_DATE = reportData.to_date;

const DATES = reportData.dates;
const APPOINTMENT_COUNTS = reportData.appointment_counts;

const TOP_MEDICINE_NAMES = reportData.top_medicine_names;
const TOP_MEDICINE_QUANTITIES = reportData.top_medicine_quantities;

// ===== Init Flatpickr =====
flatpickr("#from_date", {
    locale: "vn",
    dateFormat: "Y-m-d",
    defaultDate: FROM_DATE
});

flatpickr("#to_date", {
    locale: "vn",
    dateFormat: "Y-m-d",
    defaultDate: TO_DATE
});

// ===== Appointments Line Chart =====
const appointmentCtx = document.getElementById("appointmentChart").getContext("2d");
const appointmentChart = new Chart(appointmentCtx, {
    type: "line",
    data: {
        labels: DATES,
        datasets: [{
            label: "Lượt khám",
            data: APPOINTMENT_COUNTS,
            backgroundColor: "rgba(54, 162, 235, 0.2)",
            borderColor: "rgba(54, 162, 235, 1)",
            borderWidth: 1,
            tension: 0.4
        }]
    },
    options: {
        responsive: true,
        plugins: {
            title: {
                display: true,
                text: "Biểu đồ lượt khám theo ngày"
            }
        },
        scales: {
            y: {
                beginAtZero: true,
                title: { display: true, text: "Số lượt khám" }
            },
            x: {
                title: { display: true, text: "Ngày" }
            }
        }
    }
});

// ===== Medicine Pie Chart =====
const medicineCtx = document.getElementById("medicineChart").getContext("2d");
const medicineChart = new Chart(medicineCtx, {
    type: "doughnut",
    data: {
        labels: TOP_MEDICINE_NAMES,
        datasets: [{
            data: TOP_MEDICINE_QUANTITIES,
            backgroundColor: [
                "rgba(255, 99, 132, 0.8)",
                "rgba(54, 162, 235, 0.8)",
                "rgba(255, 206, 86, 0.8)",
                "rgba(75, 192, 192, 0.8)",
                "rgba(153, 102, 255, 0.8)"
            ],
            borderWidth: 1
        }]
    },
    options: {
        responsive: true,
        plugins: {
            title: {
                display: true,
                text: "Top 5 thuốc bán chạy"
            },
            legend: {
                position: "bottom"
            }
        }
    }
});

// ===== Export Charts =====
window.exportChart = function (format) {
    const appointmentURL = appointmentChart.toBase64Image(`image/${format}`);
    const medicineURL = medicineChart.toBase64Image(`image/${format}`);

    const link1 = document.createElement("a");
    link1.download = `appointment_chart.${format}`;
    link1.href = appointmentURL;
    link1.click();

    const link2 = document.createElement("a");
    link2.download = `medicine_chart.${format}`;
    link2.href = medicineURL;
    link2.click();
};