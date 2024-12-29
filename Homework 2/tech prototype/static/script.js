// This function is called when the page loads to dynamically fetch stock tickers
window.onload = function() {
    fetch('/api/issuers')  // Make a GET request to fetch the list of stock tickers
        .then(response => response.json())
        .then(issuers => {
            const issuerSelect = document.getElementById("issuer");
            issuers.forEach(issuer => {
                const option = document.createElement("option");
                option.value = issuer.code;
                option.text = issuer.name;  // Use issuer name or code
                issuerSelect.appendChild(option);
            });
        })
        .catch(error => console.error('Error fetching issuers:', error));
};

// Helper function to convert Macedonian price format (1.234,56) to a number (1234.56)
function formatPrice(price) {
    // If price is already a number, return it directly
    if (typeof price === 'number') {
        return price;
    }
    
    // If price is a string
    if (typeof price === 'string') {
        // Remove thousand separators (dots)
        // Replace comma with dot for decimal
        let cleanedPrice = price.replace(/\./g, '').replace(',', '.');
        
        return parseFloat(cleanedPrice);
    }
    
    // If price is undefined or null, return 0
    return 0;
}


// Function to fetch stock data for the selected issuer and date range
function fetchStockData() {
    const selectedIssuer = document.getElementById("issuer").value;
    const fromDate = document.getElementById("from-date").value;
    const toDate = document.getElementById("to-date").value;

    if (!selectedIssuer) {
        alert("Please select an issuer.");
        return;
    }

    if (!fromDate || !toDate) {
        alert("Please select both 'From' and 'To' dates.");
        return;
    }

    // Fetch the stock data from the API
    fetch(`/api/getStockData?issuer=${selectedIssuer}&from=${fromDate}&to=${toDate}`)
        .then(response => response.json())
        .then(data => {
            const stockInfo = document.getElementById("stock-info");

            if (data && data.length > 0) {
                let tableContent = `
                    <h3>Stock Information for ${selectedIssuer}</h3>
                    <table border="1">
                        <thead>
                            <tr>
                                <th>Date</th>
                                <th>Price</th>
                                <th>Volume</th>
                            </tr>
                        </thead>
                        <tbody>
                `;

                // Loop through the data and log each stock entry
                data.forEach(stock => {
                    console.log(stock); // Log the entire stock data to check its structure

                    // Format the price before displaying it
                    const formattedPrice = formatPrice(stock.lastTradePrice);
                    const volume = stock.volume || 0; // Ensure volume is displayed correctly

                    // Add a row for this stock data to the table
                    tableContent += `
                        <tr>
                            <td>${stock.date}</td>
                            <td>${formattedPrice}</td>
                            <td>${volume}</td>
                        </tr>
                    `;
                });

                tableContent += `</tbody></table>`;
                stockInfo.innerHTML = tableContent;
            } else {
                stockInfo.innerHTML = '<p>No data available for the selected period or issuer.</p>';
            }
        })
        .catch(error => console.error('Error fetching stock data:', error));
}
