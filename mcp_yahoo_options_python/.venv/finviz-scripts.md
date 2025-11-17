## get tickers from screens
Array.from(document.querySelectorAll("tr.styled-row a.tab-link")).map(ele => ele.innerText).join(",")




