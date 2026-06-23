const DATA_URL = window.LUNCH_DATA_URL || './data/site-data.json';
const SHEET_URL = window.LUNCH_SHEET_URL || '';

function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

async function loadData() {
  const response = await fetch(`${DATA_URL}?t=${Date.now()}`, { cache: 'no-store' });
  if (!response.ok) {
    throw new Error(`데이터 파일을 불러오지 못했습니다. (${response.status})`);
  }
  return response.json();
}

function setStatus(type, message) {
  const node = document.getElementById('status-message');
  node.className = `status-message ${type}`;
  node.textContent = message;
}

function renderConfig(data) {
  document.title = data.title || '점심 추천';
  document.getElementById('config-info').textContent =
    `${data.dong_name || '기준 지역'} 기준, 구글 시트와 카카오 데이터를 바탕으로 만든 오늘 점심 추천입니다.`;
  document.getElementById('base-address-input').value = data.base_address || '';
  document.getElementById('radius-input').value = `${data.search_radius_meters || 1500}m`;
  document.getElementById('generated-at').textContent = data.generated_at ? `업데이트: ${data.generated_at}` : '';

  const button = document.getElementById('sheet-open-btn');
  button.dataset.sheetUrl = data.sheet_url || SHEET_URL;
  button.disabled = !(data.sheet_url || SHEET_URL);
}

function renderWeather(data) {
  const weather = data.weather || {};
  const iconMap = {
    rainy: '☔',
    clear: '☀',
    hot: '🌡',
    cold: '❄',
    unknown: '⛅',
  };

  document.getElementById('weather-content').innerHTML = `
    <div class="weather-row">
      <div class="weather-main">
        <div class="weather-icon">${iconMap[weather.category] || '⛅'}</div>
        <div>
          <strong>오늘 점심 날씨: ${escapeHtml(weather.summary || '정보 없음')}</strong>
          <p>기온 ${escapeHtml(weather.temperature_c ?? '-')}°C</p>
          <p>${escapeHtml(weather.note || '')}</p>
        </div>
      </div>
      <div class="api-badge">${escapeHtml(data.dong_name || '동 정보 없음')}</div>
    </div>
  `;
}

function recommendationCard(item) {
  const calories = item.estimated_calories ? `${item.estimated_calories}kcal` : '추정 불가';

  return `
    <article class="card restaurant-card">
      <div class="pill">${escapeHtml(item.recommendation_type)}</div>
      <h3>${escapeHtml(item.name)}</h3>
      <dl class="meta-grid">
        <div><dt>카테고리</dt><dd>${escapeHtml(item.category)}</dd></div>
        <div><dt>거리</dt><dd>${escapeHtml(item.distance_m)}m</dd></div>
        <div><dt>점수</dt><dd>${escapeHtml(item.score)}</dd></div>
        <div><dt>예산</dt><dd>${escapeHtml(item.price_level)}</dd></div>
        <div><dt>메인 메뉴</dt><dd>${escapeHtml(item.main_menu || '추정 불가')}</dd></div>
        <div><dt>칼로리</dt><dd>${escapeHtml(calories)}</dd></div>
      </dl>
      <p class="reason">${escapeHtml(item.reason)}</p>
    </article>
  `;
}

function renderRecommendations(items) {
  const node = document.getElementById('recommendations');
  if (!items || !items.length) {
    node.innerHTML = '<p class="loading">추천할 식당이 없습니다.</p>';
    return;
  }
  node.innerHTML = items.map((item) => recommendationCard(item)).join('');
}

function renderVisits(visits) {
  const node = document.getElementById('visits');
  if (!visits || !visits.length) {
    node.innerHTML = '<p class="loading">아직 방문 기록이 없습니다.</p>';
    return;
  }

  node.innerHTML = visits
    .map(
      (visit) => `
        <div class="list-item">
          <strong>${escapeHtml(visit.restaurant_name)}</strong>
          <span>${escapeHtml(visit.visited_on)} · ${escapeHtml(visit.meal_type)} · 당일 ${escapeHtml(visit.visit_count)}회 · 누적 ${escapeHtml(visit.total_visit_count)}회</span>
        </div>
      `
    )
    .join('');
}

async function refreshData() {
  try {
    setStatus('saving', '최신 데이터를 불러오는 중입니다...');
    const data = await loadData();
    renderConfig(data);
    renderWeather(data);
    renderRecommendations(data.recommendations || []);
    renderVisits(data.visits || []);
    setStatus('success', '최신 데이터로 새로고침했습니다.');
  } catch (error) {
    setStatus('error', error.message);
  }
}

function openSheet() {
  const dataUrl = document.getElementById('sheet-open-btn').dataset.sheetUrl || SHEET_URL;
  if (!dataUrl) {
    setStatus('error', '구글 시트 주소가 아직 설정되지 않았습니다.');
    return;
  }
  window.open(dataUrl, '_blank', 'noopener,noreferrer');
}

document.addEventListener('DOMContentLoaded', async () => {
  try {
    const data = await loadData();
    renderConfig(data);
    renderWeather(data);
    renderRecommendations(data.recommendations || []);
    renderVisits(data.visits || []);
    setStatus('success', 'GitHub Pages 데이터를 불러왔습니다.');
  } catch (error) {
    setStatus('error', error.message);
  }
});
