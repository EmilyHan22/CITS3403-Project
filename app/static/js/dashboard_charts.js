// static/js/dashboard_charts.js

function genreBarChart(xArray, yArray) {
    const genreData = [{
        x: xArray,
        y: yArray,
        type: "bar",
        orientation: "h",
    }];
    const layout = {
        title: "Genre Breakdown",
        plot_bgcolor: 'rgba(255,255,255,0.3)',
        paper_bgcolor: 'rgba(0,0,0,0)'
    };
    Plotly.newPlot("horizontal-barchart", genreData, layout);
}

function listenLineGraph(xLabels, yValues) {
    const listenData = [{
        x: xLabels,
        y: yValues,
        type: "scatter",
        mode: "lines+markers",
        line: { width: 3 },
        marker: { size: 7, symbol: "circle" }
    }];
    const layout = {
        xaxis: { title: "Week" },
        yaxis: { title: "Listen Time (min)" },
        title: "Listening Time by Week",
        plot_bgcolor: 'rgba(255,255,255,0.3)',
        paper_bgcolor: 'rgba(0,0,0,0)'
    };
    Plotly.newPlot("listen-line-graph", listenData, layout);
}

document.addEventListener('DOMContentLoaded', () => {
    fetch("/api/visualise-data")
      .then(resp => resp.json())
      .then(data => {
        // genre
        const times   = data.genreBreakdown.map(d => d.time);
        const genres  = data.genreBreakdown.map(d => d.genre);
        genreBarChart(times, genres);

        // weekly
        const weeks = data.weeklyListening.map(d => d.week);
        const mins  = data.weeklyListening.map(d => d.time);
        listenLineGraph(weeks, mins);
      })
      .catch(err => console.error("Dashboard data error:", err));
});
