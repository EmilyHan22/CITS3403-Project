function genreBarChart() {
    "Creates horizontal bar chart for time listened to each genre"
    const xArray = [67, 43, 11, 34, 7] /*time*/
    const yArray = ["Business", "Psychology", "Education", "Philosophy", "Sport"] /*genre*/
    const genreData = [{
        x: xArray,
        y: yArray,
        type: "bar",
        orientation: "h",
        marker: {color:"rgba(136, 6, 116, 0.6)"}
    }];
    const layout = { title: "Genre Breakdown"};
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
        type: "scatter"
    }];

    const layout = {
        xaxis: {range: [0, 10], title: "Time (Weeks)"},
        yaxis: {range: [0, 100], title: "ListenTime (Min)"},
        title: "Listening Times Over the Weeks"
    };

    Plotly.newPlot("listen-line-graph", listenData, layout)
}

// Call the charts to when DOM is ready 
document.addEventListener('DOMContentLoaded', () => {
    genreBarChart();
    listenLineGraph();
});
