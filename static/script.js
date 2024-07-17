function getSessionId() {
    let sessionId = localStorage.getItem('session_id');
    if (!sessionId) {
        sessionId = crypto.randomUUID();
        localStorage.setItem('session_id', sessionId);
    }
    return sessionId;
}

async function fetchUserHistory() {
    const response = await fetch('/history', {
        headers: {
            'session_id': getSessionId()
        }
    });
    const data = await response.json();
    return data.history;
}

async function fetchSuggestions() {
    const input = document.getElementById('city-input');
    const query = input.value;
    if (query.length < 3) {
        document.getElementById('suggestions').innerHTML = '';
        return;
    }

    const response = await fetch(`/autocomplete?query=${query}`, {
        headers: {
            'session_id': getSessionId()
        }
    });
    const suggestions = await response.json();
    const suggestionsList = document.getElementById('suggestions');
    suggestionsList.innerHTML = '';

    suggestions.forEach(suggestion => {
        const li = document.createElement('li');
        li.textContent = suggestion.description;
        li.addEventListener('click', () => {
            input.value = suggestion.description;
            suggestionsList.innerHTML = '';
        });
        suggestionsList.appendChild(li);
    });
}

function extractCityName(fullLocation) {
    return fullLocation.split(',')[0];
}

async function fetchWeather(city) {
    const cityName = extractCityName(city);
    const response = await fetch(`/weather?city=${encodeURIComponent(cityName)}`, {
        headers: {
            'session_id': getSessionId()
        }
    });
    const weatherData = await response.json();
    const weatherInfo = document.getElementById('weather-info');

    let forecastHtml = '<h2>Weather in ' + city + '</h2>';
    forecastHtml += '<table>';
    forecastHtml += '<tr><th>Date</th>';

    weatherData.forecast.time.forEach(date => {
        forecastHtml += `<th>${formatDate(date)}</th>`;
    });
    forecastHtml += '</tr>';
    forecastHtml += '<tr><td>min t°C</td>';
    weatherData.forecast.temperature_2m_min.forEach(temp => {
        forecastHtml += `<td>${temp} °C</td>`;
    });
    forecastHtml += '</tr>';
    forecastHtml += '<tr><td>max t°C</td>';
    weatherData.forecast.temperature_2m_max.forEach(temp => {
        forecastHtml += `<td>${temp} °C</td>`;
    });
    forecastHtml += '</tr>';
    forecastHtml += '</table>';

    weatherInfo.innerHTML = forecastHtml;
}

function formatDate(dateString) {
    const date = new Date(dateString);
    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const year = String(date.getFullYear()).slice(-2);
    return `${day}.${month}.${year}`;
}

document.addEventListener("DOMContentLoaded", function () {
    const input = document.getElementById('city-input');
    input.addEventListener('focus', async function() {
        const history = await fetchUserHistory();
        if (history.length > 0) {
            const suggestionsList = document.getElementById('suggestions');
            suggestionsList.innerHTML = '';
            history.forEach(item => {
                const li = document.createElement('li');
                li.textContent = item;
                li.addEventListener('click', () => {
                    input.value = item;
                    suggestionsList.innerHTML = '';
                });
                suggestionsList.appendChild(li);
            });
        }
    });

    input.addEventListener('input', fetchSuggestions);

    document.getElementById('weather-form').addEventListener('submit', function (event) {
        event.preventDefault();
        const city = input.value;
        fetchWeather(city);
        document.getElementById('suggestions').innerHTML = ''; // Скрыть подсказки при нажатии на кнопку
    });
});
