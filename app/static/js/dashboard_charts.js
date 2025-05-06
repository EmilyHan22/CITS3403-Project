function genreBarChart() {
    "Creates horizontal bar chart for time listened to each genre"
    const xArray = [67, 43, 11, 34, 7] /*time*/
    const yArray = ["Business", "Psychology", "Education", "Philosophy", "Sport"] /*genre*/
    const genreData = [{
        x: xArray,
        y: yArray,
        type: "bar",
        orientation: "h",
        marker: {color:"rgba(136, 6, 116, 0.7)"}
    }];
    const layout = { 
        title: "Genre Breakdown",
        plot_bgcolor: 'rgba(255, 255, 255, 0.3)',
        paper_bgcolor: 'rgba(0, 0, 0, 0)'
    };
    Plotly.newPlot("horizontal-barchart", genreData, layout)

}

function listenLineGraph() {
    "Creates a line graph for total weekly time"
    // Data
    const xTimeStamp = [1, 2, 3, 4, 5, 6];
    const yListenTime = [20, 40, 30, 27, 90, 92];

    const listenData = [{
        x: xTimeStamp,
        y: yListenTime,
        modes: "lines",
        type: "scatter",
        line: {
            color: "rgba(136, 6, 116, 0.6)",
            width: 3,
            //dash: 'dashdot'  // solid, dot, dash, dashdot
          },
          marker: {
            color: "rgba(136, 6, 116, 1)",
            size: 7,
            symbol: "circle", // many marker shapes

          }
    }];

    const layout = {
        xaxis: {range: [0, 8], title: "Time (Weeks)"},
        yaxis: {range: [0, 100], title: "ListenTime (Min)"},
        title: "Listening Times Over the Weeks",
        plot_bgcolor: 'rgba(255, 255, 255, 0.3)',
        paper_bgcolor: 'rgba(0, 0, 0, 0)',
    };

    Plotly.newPlot("listen-line-graph", listenData, layout)
}

// Call the charts to when DOM is ready 
document.addEventListener('DOMContentLoaded', () => {
    genreBarChart();
    listenLineGraph();
});
