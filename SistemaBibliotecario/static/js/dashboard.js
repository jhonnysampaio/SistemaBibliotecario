(() => {
    const canvas = document.querySelector("#loans-chart");

    if (!canvas || typeof Chart === "undefined") {
        return;
    }

    const labelsElement = document.querySelector("#grafico-labels");
    const valuesElement = document.querySelector("#grafico-valores");

    if (!labelsElement || !valuesElement) {
        return;
    }

    const labels = JSON.parse(labelsElement.textContent);
    const values = JSON.parse(valuesElement.textContent);

    new Chart(canvas, {
        type: "line",
        data: {
            labels,
            datasets: [
                {
                    label: "Empréstimos",
                    data: values,
                    borderColor: "#173f35",
                    backgroundColor: "rgba(118, 151, 129, 0.18)",
                    fill: true,
                    tension: 0.35,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false,
                },
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0,
                    },
                },
            },
        },
    });
})();
