// static/js/dashboard_charts.js

// static/js/dashboard_charts.js

function genreBarChart(xArray, yArray) {
  // 1) build a parallel array of abbreviated labels
  const abbr = yArray.map(g => {
    // if it has “and” or “&”, split on that and keep first letters joined by “&”
    if (/\band\b|&/i.test(g)) {
      const parts = g.split(/\s+and\s+|\s*&\s*/i).map(s=>s.trim()).filter(Boolean);
      if (parts.length >= 2) {
        return parts.map(p => p.charAt(0).toUpperCase()).join('&');
      }
    }
    // otherwise leave it whole
    return g;
  });

  // 2) trace uses the full genre names under the hood, but we’ll swap in abbr for the ticks
  const trace = {
    x: xArray,
    y: yArray,
    type: "bar",
    orientation: "h",
    marker: { color: "rgba(136, 6, 116, 0.7)" },
    customdata: yArray,  
    hovertemplate: "%{customdata}: %{x} min<extra></extra>"
  };

  // 3) layout with custom ticktext/tickvals
  const layout = {
    title: {
      text: "Genre Breakdown",
      font: { family: "Poppins, sans-serif", size: 20 },
      x: 0
    },
    margin: { l: 100, r: 40, t: 60, b: 60 },
    plot_bgcolor: "transparent",
    paper_bgcolor: "transparent",
    xaxis: {
      title: {
        text: "Time (minutes)",
        font: { family: "Poppins, sans-serif", size: 16 }
      },
      tickfont: { family: "Poppins, sans-serif", size: 12 },
      showgrid: true,
      gridcolor: "rgba(200,200,200,0.2)"
    },
    yaxis: {
      title: {
        text: "Genres",
        font: { family: "Poppins, sans-serif", size: 16 }
      },
      tickmode: "array",
      tickvals: yArray,
      ticktext: abbr,
      tickfont: { family: "Poppins, sans-serif", size: 14 },
      automargin: true,
      ticklabelpadding: 5,
      ticks: "outside",
      showgrid: false
    }
  };

  Plotly.newPlot("horizontal-barchart", [trace], layout, { responsive: true });
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
