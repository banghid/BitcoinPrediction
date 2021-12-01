const prediksictx = document.getElementById('prediksiChart').getContext('2d');
const prediksiChart = new Chart(prediksictx, {
    type: 'line',
    data: {
        labels: [],
        datasets: [{
            label: ['Original Data'],
            data: [],
            backgroundColor: [
                'rgba(255, 99, 132, 0.2)',
                // 'rgba(54, 162, 235, 0.2)',
                // 'rgba(255, 206, 86, 0.2)',
                // 'rgba(75, 192, 192, 0.2)',
                // 'rgba(153, 102, 255, 0.2)',
                // 'rgba(255, 159, 64, 0.2)'
            ],
            borderColor: [
                'rgba(255, 99, 132, 1)',
                // 'rgba(54, 162, 235, 1)',
                // 'rgba(255, 206, 86, 1)',
                // 'rgba(75, 192, 192, 1)',
                // 'rgba(153, 102, 255, 1)',
                // 'rgba(255, 159, 64, 1)'
            ],
            borderWidth: 1
        },{
            label: 'Predicted',
            data: [],
            backgroundColor: [
                // 'rgba(255, 99, 132, 0.2)',
                'rgba(54, 162, 235, 0.2)',
                // 'rgba(255, 206, 86, 0.2)',
                // 'rgba(75, 192, 192, 0.2)',
                // 'rgba(153, 102, 255, 0.2)',
                // 'rgba(255, 159, 64, 0.2)'
            ],
            borderColor: [
                // 'rgba(255, 99, 132, 1)',
                'rgba(54, 162, 235, 1)',
                // 'rgba(255, 206, 86, 1)',
                // 'rgba(75, 192, 192, 1)',
                // 'rgba(153, 102, 255, 1)',
                // 'rgba(255, 159, 64, 1)'
            ],
            borderWidth: 1
        }]
    },
    options: {
        scales: {
            y: {
                beginAtZero: true
            }
        }
    }
});

var day1 = document.getElementById("day1");
var day7 = document.getElementById("day7");
var day30 = document.getElementById("day30");

var heat_data = new Array();

$.ajax({
    type: "GET",
    url: "/get_corr",
    data: JSON.stringify(),
    contentType: "application/json",
    dataType: "json",
    success: function(response) {
        data = response;
        
        Object.values(data).forEach(val => {

            temp = [ 
                val.open,
                val.high,
                val.low,
                val.close,
                val.volume,
                val.marketcap,
                val.gold_price,
                val.gtrend
            ];
            
            heat_data.push(temp);

        });

    
        var heatmap_config = [
            {
                z: heat_data,
                x: ['open', 'high', 'low', 'close','volume', 'marketcap', 'gold_price', 'gtrend'],
                y: ['open', 'high', 'low', 'close','volume', 'marketcap', 'gold_price', 'gtrend'],
                type: 'heatmap',
                hoverongaps: false,
            }
            ];
        // console.log(heatmap_config);
            Plotly.newPlot('heatMap', heatmap_config);
    }
})


function predictFuture(length = 1){
    var predict_length = length;

    switch(length){
        case 1:
            day1.classList.add("filter-active");
            day7.classList.remove("filter-active");
            day30.classList.remove("filter-active");
            break;
        case 7:
            day1.classList.remove("filter-active");
            day7.classList.add("filter-active");
            day30.classList.remove("filter-active");
            break;
        case 30:
            day1.classList.remove("filter-active");
            day7.classList.remove("filter-active");
            day30.classList.add("filter-active");
    }
    

    $.ajax({
        type: "POST",
        url: "/predict",
        data: JSON.stringify(predict_length),
        contentType: "application/json",
        dataType: "json",
        success: function(response){
            data = response;            

            prediksiChart.data.labels = []
            prediksiChart.data.datasets.forEach((dataset) => {
                dataset.data = []
            });
            prediksiChart.update();
            counter_index = 0;
            Object.values(data.date).forEach(val => {
                if (counter_index > length){
                    timestamp = new Date(val);
                    prediksiChart.data.labels.push(timestamp.toDateString());
                }     
                counter_index +=1;          
            });
            counter_index = 0;
            Object.values(data.Date).forEach(val => {
                if (counter_index < length){
                    timestamp = new Date(val);
                    prediksiChart.data.labels.push(timestamp.toDateString());
                }
                counter_index +=1; 
            })
            
            counter = 0;
            Object.size = function(obj){
                var size = 0,
                    key;
                for (key in obj) {
                    if (obj.hasOwnProperty(key)) size++;
                }
                return size;
            }
            predicted_null_length = Object.size(data.Open) - length;
            console.log(predicted_null_length);
            prediksiChart.data.datasets.forEach((dataset) => {
                if (counter == 1){
                    open_data = [];
                    length_counter = 0;
                    counter_index = 0;
                    Object.values(data.Open).forEach(val => {
                        if(counter_index < length){
                            open_data.push(val);
                        } else if(length_counter < predicted_null_length){
                            dataset.data.push(null);
                        }else{
                            open_data.forEach(val => {
                                dataset.data.push(val);
                            })
                        }

                        length_counter += 1;
                        counter_index += 1;
                    });
                }
                else {                   
                    counter_index = 0; 
                    Object.values(data.open).forEach(val => {
                        if(counter_index > length){
                            dataset.data.push(val);                            
                        }
                        counter_index +=1;
                    });
                    
                }
                
                counter += 1;
                
            });
            prediksiChart.update();
        }
    });
    
    
    
}