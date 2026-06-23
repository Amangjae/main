// ============ API 호출 함수 ============
const API_BASE = '/api';

async function apiCall(endpoint, method = 'GET', data = null) {
    try {
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json',
            },
        };

        if (data && (method === 'POST' || method === 'PUT')) {
            options.body = JSON.stringify(data);
        }

        const response = await fetch(`${API_BASE}${endpoint}`, options);
        
        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error(`API Call Failed: ${endpoint}`, error);
        throw error;
    }
}

// ============ 데이터 로드 함수 ============
async function loadConfig() {
    try {
        const config = await apiCall('/config');
        const configInfo = document.getElementById('config-info');
        configInfo.textContent = `기준 주소: ${config.base_address} | 반경 ${config.search_radius_meters}m 식당 대상`;
        
        // Kakao API 버튼 활성화/비활성화
        const kakaoBtn = document.getElementById('kakao-btn');
        if (!config.has_kakao_api) {
            kakaoBtn.disabled = true;
            kakaoBtn.title = 'KAKAO_REST_API_KEY가 설정되지 않았습니다.';
        }
    } catch (error) {
        console.error('Failed to load config:', error);
    }
}

async function loadWeather() {
    try {
        const data = await apiCall('/weather');
        const weatherContent = document.getElementById('weather-content');
        
        const iconMap = {
            'rainy': '☔',
            'clear': '🌤️',
            'hot': '☀️',
            'cold': '❄️',
            'unknown': '🌥️',
        };

        const icon = iconMap[data.category] || '🌥️';
        const html = `
            <div style="display: flex; align-items: center; gap: 20px;">
                <span class="weather-icon">${icon}</span>
                <div>
                    <h3 style="margin: 0;">오늘 점심 날씨: ${data.summary}</h3>
                    <p style="margin: 5px 0;">기온: ${data.temperature_c}°C</p>
                    <p style="margin: 5px 0;">추천 포인트: ${data.note}</p>
                </div>
            </div>
        `;
        weatherContent.innerHTML = html;
    } catch (error) {
        console.error('Failed to load weather:', error);
        document.getElementById('weather-content').innerHTML = 
            '<p style="color: red;">날씨 정보를 가져올 수 없습니다.</p>';
    }
}

async function loadRecommendations() {
    try {
        const data = await apiCall('/recommendations');
        const container = document.getElementById('recommendations');

        if (!data.recommendations || data.recommendations.length === 0) {
            container.innerHTML = '<p class="loading">추천할 식당이 없습니다. 초기 데이터를 준비해주세요.</p>';
            return;
        }

        const html = data.recommendations.map(item => `
            <div class="restaurant-card">
                <h4>${item.name}</h4>
                <div class="restaurant-info">
                    <p><strong>카테고리:</strong> ${item.category}</p>
                    <p><strong>거리:</strong> 약 ${item.distance_m}m</p>
                    <p><strong>추천 유형:</strong> ${item.recommendation_type}</p>
                    <p><span class="score">점수: ${item.score}</span></p>
                    <p><strong>예상 예산:</strong> ${item.price_level}</p>
                </div>
                <div class="reason">💡 ${item.reason}</div>
                <button class="btn btn-visit" onclick="recordVisit(${item.id}, '${item.name}')">
                    ✓ 방문 기록 추가
                </button>
            </div>
        `).join('');

        container.innerHTML = html;
    } catch (error) {
        console.error('Failed to load recommendations:', error);
        document.getElementById('recommendations').innerHTML =
            '<p style="color: red;">추천 식당을 가져올 수 없습니다.</p>';
    }
}

async function loadVisits() {
    try {
        const data = await apiCall('/visits');
        const container = document.getElementById('visits');

        if (!data.visits || data.visits.length === 0) {
            container.innerHTML = '<p class="loading">아직 방문 이력이 없습니다.</p>';
            return;
        }

        const html = data.visits.map(visit => `
            <div class="visit-item">
                <strong>${visit.restaurant_name}</strong><br>
                <small>${visit.visited_on} | ${visit.meal_type} | 누적 ${visit.visit_count}회 방문</small>
            </div>
        `).join('');

        container.innerHTML = html;
    } catch (error) {
        console.error('Failed to load visits:', error);
        document.getElementById('visits').innerHTML =
            '<p style="color: red;">방문 이력을 가져올 수 없습니다.</p>';
    }
}

async function loadRestaurants() {
    try {
        const data = await apiCall('/restaurants');
        const container = document.getElementById('restaurants');

        if (!data.restaurants || data.restaurants.length === 0) {
            container.innerHTML = '<p class="loading">등록된 식당이 없습니다.</p>';
            return;
        }

        const html = `
            <p><strong>총 ${data.count}곳</strong></p>
            ${data.restaurants.map(restaurant => {
                const address = restaurant.road_address || restaurant.address || '-';
                const source = restaurant.source || 'sample';
                return `
                    <div class="restaurant-item">
                        <strong>${restaurant.name}</strong>
                        <small>${restaurant.category} | ${restaurant.distance_m}m</small>
                        <small>${address}</small>
                        <small style="color: #999;">source=${source}</small>
                        ${restaurant.place_url ? `<small><a href="${restaurant.place_url}" target="_blank">상세보기</a></small>` : ''}
                    </div>
                `;
            }).join('')}
        `;

        container.innerHTML = html;
    } catch (error) {
        console.error('Failed to load restaurants:', error);
        document.getElementById('restaurants').innerHTML =
            '<p style="color: red;">식당 목록을 가져올 수 없습니다.</p>';
    }
}

async function loadAllData() {
    console.log('Loading all data...');
    await Promise.all([
        loadConfig(),
        loadWeather(),
        loadRecommendations(),
        loadVisits(),
        loadRestaurants(),
    ]);
}

// ============ 액션 함수 ============
async function recordVisit(restaurantId, restaurantName) {
    try {
        showStatus('saving', `${restaurantName} 방문 기록 중...`);
        await apiCall(`/visit/${restaurantId}`, 'POST');
        showStatus('success', `${restaurantName} 방문 이력이 저장되었습니다.`);
        await loadRecommendations();
        await loadVisits();
    } catch (error) {
        showStatus('error', `방문 기록 저장 실패: ${error.message}`);
    }
}

async function importFromKakao() {
    if (confirm('카카오 API로부터 주변 식당을 가져오시겠습니까?')) {
        try {
            showStatus('saving', '카카오 API에서 데이터를 가져오는 중...');
            const result = await apiCall('/import-kakao', 'POST');
            
            if (result.status === 'success') {
                showStatus('success', `새로 추가: ${result.inserted}곳 | 중복: ${result.skipped}곳`);
                await loadRestaurants();
            } else {
                showStatus('error', result.message);
            }
        } catch (error) {
            showStatus('error', `카카오 임포트 실패: ${error.message}`);
        }
    }
}

async function resetData() {
    if (confirm('초기 데이터로 리셋하시겠습니까? (기존 방문 이력이 삭제됩니다)')) {
        try {
            showStatus('saving', '데이터를 리셋 중...');
            const result = await apiCall('/reset-data', 'POST');
            
            if (result.status === 'success') {
                showStatus('success', result.message);
                await loadAllData();
            } else {
                showStatus('error', result.message);
            }
        } catch (error) {
            showStatus('error', `리셋 실패: ${error.message}`);
        }
    }
}

async function refreshData() {
    try {
        showStatus('saving', '데이터를 새로고침 중...');
        await loadAllData();
        showStatus('success', '데이터가 새로고침되었습니다.');
    } catch (error) {
        showStatus('error', `새로고침 실패: ${error.message}`);
    }
}

async function clearCache() {
    try {
        showStatus('saving', '캐시를 초기화 중...');
        const result = await apiCall('/clear-cache', 'POST');
        
        if (result.status === 'success') {
            showStatus('success', result.message);
            await loadAllData();
        } else {
            showStatus('error', result.message);
        }
    } catch (error) {
        showStatus('error', `캐시 초기화 실패: ${error.message}`);
    }
}

// ============ UI 함수 ============
function showStatus(type, message) {
    const statusElement = document.getElementById('status-message');
    statusElement.textContent = message;
    statusElement.className = `status-message ${type}`;
    
    if (type !== 'saving') {
        setTimeout(() => {
            statusElement.textContent = '';
            statusElement.className = 'status-message';
        }, 3000);
    }
}

function toggleExpander(button) {
    button.classList.toggle('active');
    const content = button.nextElementSibling;
    content.classList.toggle('active');
}

// ============ 초기화 ============
document.addEventListener('DOMContentLoaded', () => {
    console.log('Page loaded, initializing...');
    loadAllData();
    
    // 5분마다 데이터 새로고침
    setInterval(() => {
        console.log('Auto-refreshing data...');
        loadAllData();
    }, 5 * 60 * 1000);
});
