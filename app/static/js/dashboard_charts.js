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

// Call the charts to when DOM is ready 
document.addEventListener('DOMContentLoaded', () => {
    genreBarChart();
});
