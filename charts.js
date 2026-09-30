let chartInstances = {};

function destroyChartIfExists(chartId) {
    if (chartInstances[chartId]) {
        chartInstances[chartId].destroy();
        delete chartInstances[chartId];
    }
}

function renderFeatureImportanceChart(canvasId, importancesMap) {
    const el = document.getElementById(canvasId);
    if (!el) return;
    destroyChartIfExists(canvasId);

    const labels = Object.keys(importancesMap).map(k => k.replace('cat__location_', 'Locality: ').replace('num__', ''));
    const values = Object.values(importancesMap).map(v => (v * 100).toFixed(1));

    const ctx = el.getContext('2d');
    chartInstances[canvasId] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Prediction Contribution Weight (%)',
                data: values,
                backgroundColor: 'rgba(99, 102, 241, 0.75)',
                borderColor: '#6366f1',
                borderWidth: 1.5,
                borderRadius: 6
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } },
                y: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } }
            }
        }
    });
}

function renderLocationPriceChart(canvasId, locSummaryMap) {
    const el = document.getElementById(canvasId);
    if (!el) return;
    destroyChartIfExists(canvasId);

    const labels = Object.keys(locSummaryMap);
    const avgRates = labels.map(loc => locSummaryMap[loc].avg_price_per_sqft);

    const ctx = el.getContext('2d');
    chartInstances[canvasId] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Avg Rate (₹/SqFt)',
                data: avgRates,
                backgroundColor: 'rgba(6, 182, 212, 0.75)',
                borderColor: '#06b6d4',
                borderWidth: 1.5,
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: { ticks: { color: '#94a3b8', maxRotation: 45 }, grid: { color: 'rgba(255,255,255,0.05)' } },
                y: { ticks: { color: '#94a3b8', callback: v => '₹' + v.toLocaleString() }, grid: { color: 'rgba(255,255,255,0.05)' } }
            }
        }
    });
}

function renderPropertyComparisonChart(canvasId, propAName, propAPrice, propBName, propBPrice) {
    const el = document.getElementById(canvasId);
    if (!el) return;
    destroyChartIfExists(canvasId);

    const ctx = el.getContext('2d');
    chartInstances[canvasId] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: [propAName, propBName],
            datasets: [{
                label: 'Estimated Price (₹ Lakhs)',
                data: [propAPrice, propBPrice],
                backgroundColor: ['rgba(99, 102, 241, 0.8)', 'rgba(16, 185, 129, 0.8)'],
                borderColor: ['#6366f1', '#10b981'],
                borderWidth: 2,
                borderRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } },
                y: { ticks: { color: '#94a3b8', callback: v => '₹' + v + 'L' }, grid: { color: 'rgba(255,255,255,0.05)' } }
            }
        }
    });
}