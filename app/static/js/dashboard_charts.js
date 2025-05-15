// static/js/dashboard_charts.js

/**
 * Horizontal bar chart of total minutes per genre.
 * Abbreviates any multi-word genres containing "and" or "&" (e.g. "Business and Economy" → "B&E").
 */
function genreBarChart(xArray, yArray) {
  // build abbreviated tick labels
  const abbr = yArray.map(g => {
    if (/\band\b|&/i.test(g)) {
      const parts = g
        .split(/\s+and\s+|\s*&\s*/i)
        .map(s => s.trim())
        .filter(Boolean);
      if (parts.length >= 2) {
        return parts.map(p => p.charAt(0).toUpperCase()).join('&');
      }
    }
    return g;
  });

  // the trace carries the full names in customdata for hover
  const trace = {
    x: xArray,
    y: yArray,
    type: 'bar',
    orientation: 'h',
    marker: { color: 'rgba(136, 6, 116, 0.7)' },
    customdata: yArray,
    hovertemplate: '%{customdata}: %{x} min<extra></extra>'
  };

  // base layout
  const layout = {
    title: {
      text: 'Genre Breakdown',
      font: { family: 'Poppins, sans-serif', size: 20 },
      x: 0
    },
    plot_bgcolor: 'transparent',
    paper_bgcolor: 'transparent',
    xaxis: {
      title: {
        text: 'Time (minutes)',
        font: { family: 'Poppins, sans-serif', size: 16 }
      },
      tickfont: { family: 'Poppins, sans-serif', size: 12 },
      showgrid: true,
      gridcolor: 'rgba(200,200,200,0.2)',
      automargin: true
    },
    yaxis: {
      title: {
        text: 'Genres',
        font: { family: 'Poppins, sans-serif', size: 16 }
      },
      tickmode: 'array',
      tickvals: yArray,
      ticktext: abbr,
      tickfont: { family: 'Poppins, sans-serif', size: 14 },
      automargin: true,
      ticklabelpadding: 5,
      ticks: 'outside',
      showgrid: false
    }
  };

  // render responsively into its container
  Plotly.newPlot(
    'horizontal-barchart',
    [trace],
    Object.assign({}, layout, {
      autosize: true,
      margin: { l: 100, r: 40, t: 60, b: 60 }
    }),
    { responsive: true }
  );
}

/**
 * Simple line+marker chart of listening time by week.
 */
function listenLineGraph(xLabels, yValues) {
  const listenData = [
    {
      x: xLabels,
      y: yValues,
      type: 'scatter',
      mode: 'lines+markers',
      line: { width: 3 },
      marker: { size: 7, symbol: 'circle' }
    }
  ];

  const layout = {
    title: {
      text: 'Listening Time by Week',
      font: { family: 'Poppins, sans-serif', size: 20 },
      x: 0.5
    },
    autosize: true,
    margin: { l: 60, r: 40, t: 60, b: 60 },
    plot_bgcolor: 'transparent',
    paper_bgcolor: 'transparent',
    xaxis: {
      title: {
        text: 'Week',
        font: { family: 'Poppins, sans-serif', size: 16 }
      },
      tickfont: { family: 'Poppins, sans-serif', size: 12 },
      automargin: true,
      showgrid: false
    },
    yaxis: {
      title: {
        text: 'Listen Time (min)',
        font: { family: 'Poppins, sans-serif', size: 16 }
      },
      tickfont: { family: 'Poppins, sans-serif', size: 12 },
      automargin: true,
      showgrid: true,
      gridcolor: 'rgba(200,200,200,0.2)'
    }
  };

  Plotly.newPlot(
    'listen-line-graph',
    listenData,
    layout,
    { responsive: true }
  );
}

// fetch the pre-computed JSON and draw both charts once the DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  fetch('/api/visualise-data')
    .then(resp => resp.json())
    .then(data => {
      const times = data.genreBreakdown.map(d => d.time);
      const genres = data.genreBreakdown.map(d => d.genre);
      genreBarChart(times, genres);

      const weeks = data.weeklyListening.map(d => d.week);
      const mins = data.weeklyListening.map(d => d.time);
      listenLineGraph(weeks, mins);
    })
    .catch(err => console.error('Dashboard data error:', err));
});
