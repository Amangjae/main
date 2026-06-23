const sampleWeather = {
  category: 'hot',
  summary: '덥고 습함',
  temperature_c: 29,
  note: '실내 좌석과 가벼운 메뉴에 가점',
};

const sampleVisits = [
  { restaurant_name: '을지로국밥', visited_on: '2026-06-20', meal_type: '점심', visit_count: 2 },
  { restaurant_name: '을지로짬뽕', visited_on: '2026-06-18', meal_type: '점심', visit_count: 1 },
  { restaurant_name: '을지로제육식당', visited_on: '2026-06-16', meal_type: '점심', visit_count: 1 },
];

const sampleRestaurants = [
  { name: '을지로국밥', category: '한식', distance_m: 250, address: '서울 중구 을지로 일대', source: 'sample' },
  { name: '을지로제육식당', category: '한식', distance_m: 430, address: '서울 중구 을지로 일대', source: 'sample' },
  { name: '을지로파스타', category: '양식', distance_m: 580, address: '서울 중구 을지로 일대', source: 'sample' },
  { name: '을지로짬뽕', category: '중식', distance_m: 640, address: '서울 중구 을지로 일대', source: 'sample' },
  { name: '명동칼국수', category: '면요리', distance_m: 780, address: '서울 중구 명동 일대', source: 'sample' },
  { name: '충무로돈까스', category: '일식', distance_m: 920, address: '서울 중구 충무로 일대', source: 'sample' },
];

const sampleRecommendations = [
  {
    name: '을지로국밥',
    category: '한식',
    distance_m: 250,
    score: 6.4,
    price_level: '보통',
    recommendation_type: '재방문 추천',
    reason: '더운 날씨를 고려했고, 가까우며 익숙한 식당입니다.',
  },
  {
    name: '을지로제육식당',
    category: '한식',
    distance_m: 430,
    score: 5.8,
    price_level: '보통',
    recommendation_type: '재방문 추천',
    reason: '든든한 점심 메뉴이고 이동 부담이 적습니다.',
  },
  {
    name: '을지로짬뽕',
    category: '중식',
    distance_m: 640,
    score: 5.3,
    price_level: '보통',
    recommendation_type: '재방문 추천',
    reason: '실내 선호와 메뉴 다양성을 함께 반영했습니다.',
  },
  {
    name: '을지로파스타',
    category: '양식',
    distance_m: 580,
    score: 4.9,
    price_level: '약간높음',
    recommendation_type: '새로운 도전',
    reason: '아직 방문 이력이 없는 신규 후보입니다.',
  },
];

function renderWeather() {
  const iconMap = {
    rainy: '🌧️',
    clear: '🌤️',
    hot: '☀️',
    cold: '🥶',
  };

  document.getElementById('weather-content').innerHTML = `
    <div class="weather-row">
      <div class="weather-icon">${iconMap[sampleWeather.category] || '🌥️'}</div>
      <div>
        <strong>오늘 점심 날씨: ${sampleWeather.summary}</strong>
        <p>기온 ${sampleWeather.temperature_c}°C</p>
        <p>${sampleWeather.note}</p>
      </div>
    </div>
  `;
}

function renderRecommendations() {
  document.getElementById('recommendations').innerHTML = sampleRecommendations
    .map(
      (item) => `
        <article class="card restaurant-card">
          <div class="pill">${item.recommendation_type}</div>
          <h3>${item.name}</h3>
          <dl class="meta-grid">
            <div><dt>카테고리</dt><dd>${item.category}</dd></div>
            <div><dt>거리</dt><dd>${item.distance_m}m</dd></div>
            <div><dt>점수</dt><dd>${item.score}</dd></div>
            <div><dt>예산</dt><dd>${item.price_level}</dd></div>
          </dl>
          <p class="reason">${item.reason}</p>
        </article>
      `
    )
    .join('');
}

function renderVisits() {
  document.getElementById('visits').innerHTML = sampleVisits
    .map(
      (visit) => `
        <div class="list-item">
          <strong>${visit.restaurant_name}</strong>
          <span>${visit.visited_on} · ${visit.meal_type} · 누적 ${visit.visit_count}회</span>
        </div>
      `
    )
    .join('');
}

function renderRestaurants() {
  document.getElementById('restaurants').innerHTML = sampleRestaurants
    .map(
      (restaurant) => `
        <div class="list-item">
          <strong>${restaurant.name}</strong>
          <span>${restaurant.category} · ${restaurant.distance_m}m · ${restaurant.address}</span>
          <span>source=${restaurant.source}</span>
        </div>
      `
    )
    .join('');
}

renderWeather();
renderRecommendations();
renderVisits();
renderRestaurants();
