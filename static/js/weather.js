/**
 * Weather App - Location & UI Management
 */

// DOM Elements
const elements = {
  loadingState: document.getElementById('loading-state'),
  permissionState: document.getElementById('permission-state'),
  weatherState: document.getElementById('weather-state'),
  loadingText: document.getElementById('loading-text'),
  grantLocationBtn: document.getElementById('grant-location'),
  permissionError: document.getElementById('permission-error'),
  toggleLocationBtn: document.getElementById('toggle-location'),
  locationModal: document.getElementById('location-modal'),
  closeModalBtn: document.getElementById('close-modal'),
  modalBackdrop: document.getElementById('modal-backdrop'),
  useCurrentLocationBtn: document.getElementById('use-current-location'),
  switchLocationModal: document.getElementById('switch-location-modal'),
  switchModalBackdrop: document.getElementById('switch-modal-backdrop'),
  switchToCurrentBtn: document.getElementById('switch-to-current'),
  keepLocationBtn: document.getElementById('keep-location'),
  addressInput: document.getElementById('address'),
  refreshBtn: document.getElementById('refresh-weather'),
  refreshModal: document.getElementById('refresh-modal'),
  refreshModalBackdrop: document.getElementById('refresh-modal-backdrop'),
  refreshCloseBtn: document.getElementById('refresh-close'),
  refreshLocationList: document.getElementById('refresh-location-list'),
  refreshStatus: document.getElementById('refresh-status'),
  dailyForecastList: document.getElementById('daily-forecast-list'),
  dayDetailModal: document.getElementById('day-detail-modal'),
  dayDetailBackdrop: document.getElementById('day-detail-backdrop'),
  dayDetailCloseBtn: document.getElementById('day-detail-close'),
  dayDetailTitle: document.getElementById('day-detail-title'),
  dayDetailSubtitle: document.getElementById('day-detail-subtitle'),
  dayDetailSummary: document.getElementById('day-detail-summary'),
  dayDetailHighLow: document.getElementById('day-detail-high-low'),
  dayDetailFeelsLike: document.getElementById('day-detail-feels-like'),
  dayDetailTempRange: document.getElementById('day-detail-temp-range'),
  dayDetailPrecipRange: document.getElementById('day-detail-precip-range'),
  dayDetailTempChart: document.getElementById('day-detail-temp-chart'),
  dayDetailPrecipChart: document.getElementById('day-detail-precip-chart'),
  dayDetailTempTooltip: document.getElementById('day-detail-temp-tooltip'),
  dayDetailPrecipTooltip: document.getElementById('day-detail-precip-tooltip'),
  dayDetailTempMarker: document.getElementById('day-detail-temp-marker'),
  dayDetailPrecipMarker: document.getElementById('day-detail-precip-marker'),
  dayDetailTimeAxis: document.getElementById('day-detail-time-axis'),
  dayDetailCharts: document.getElementById('day-detail-charts'),
  dayDetailEmpty: document.getElementById('day-detail-empty'),
};

// Configuration
const CONFIG = {
  LOCATION_DELTA_THRESHOLD: 0.03,
  GEOLOCATION_OPTIONS: {
    enableHighAccuracy: false,
    timeout: 10000,
    maximumAge: 60000,
  },
};

// State
let pendingSwitchLocation = null;
let dailyDetailsMap = new Map();
let currentDayDetails = null;
let currentDayUnit = '';

/**
 * Show a specific UI state and hide others
 */
function showState(state) {
  elements.loadingState?.classList.add('hidden');
  elements.permissionState?.classList.add('hidden');
  elements.weatherState?.classList.add('hidden');
  state?.classList.remove('hidden');
}

/**
 * Open the location search modal
 */
function openModal() {
  elements.locationModal?.classList.remove('hidden');
  elements.addressInput?.focus();
}

/**
 * Close the location search modal
 */
function closeModal() {
  elements.locationModal?.classList.add('hidden');
}

/**
 * Open the switch location modal
 */
function openSwitchModal(coords) {
  pendingSwitchLocation = coords;
  elements.switchLocationModal?.classList.remove('hidden');
}

/**
 * Close the switch location modal
 */
function closeSwitchModal() {
  elements.switchLocationModal?.classList.add('hidden');
  pendingSwitchLocation = null;
}

/**
 * Get a cookie value by name
 */
function getCookieValue(name) {
  const match = document.cookie.split('; ').find((row) => row.startsWith(`${name}=`));
  return match ? decodeURIComponent(match.split('=')[1]) : null;
}

/**
 * Get cached location from cookies
 */
function getCachedLocation() {
  const lat = Number.parseFloat(getCookieValue('last_lat'));
  const lon = Number.parseFloat(getCookieValue('last_lon'));
  if (!Number.isFinite(lat) || !Number.isFinite(lon)) {
    return null;
  }
  return { lat, lon };
}

/**
 * Check if two locations are significantly different
 */
function isSignificantlyDifferent(a, b) {
  return (
    Math.abs(a.lat - b.lat) > CONFIG.LOCATION_DELTA_THRESHOLD ||
    Math.abs(a.lon - b.lon) > CONFIG.LOCATION_DELTA_THRESHOLD
  );
}

/**
 * Redirect to a location
 */
function redirectToLocation(coords) {
  const latValue = Number(coords.latitude ?? coords.lat);
  const lonValue = Number(coords.longitude ?? coords.lon);
  if (!Number.isFinite(latValue) || !Number.isFinite(lonValue)) {
    return;
  }
  const lat = latValue.toFixed(4);
  const lon = lonValue.toFixed(4);
  window.location = `/?lat=${lat}&lon=${lon}`;
}

/**
 * Request user's location
 */
function requestLocation({ showLoading = true, onSuccess } = {}) {
  if (showLoading) {
    showState(elements.loadingState);
    if (elements.loadingText) {
      elements.loadingText.textContent = 'Detecting your location...';
    }
  }

  const handleSuccess = onSuccess || ((coords) => redirectToLocation(coords));

  navigator.geolocation.getCurrentPosition(
    (position) => {
      if (showLoading && elements.loadingText) {
        elements.loadingText.textContent = 'Loading weather...';
      }
      handleSuccess(position.coords);
    },
    (error) => {
      if (!showLoading) return;
      
      if (error.code === error.PERMISSION_DENIED) {
        showState(elements.permissionState);
      } else {
        if (elements.permissionError) {
          elements.permissionError.textContent = error.message || 'Unable to get location';
          elements.permissionError.classList.remove('hidden');
        }
        showState(elements.permissionState);
      }
    },
    CONFIG.GEOLOCATION_OPTIONS
  );
}

/**
 * Open the refresh cache modal
 */
function openRefreshModal() {
  elements.refreshModal?.classList.remove('hidden');
  elements.refreshStatus?.classList.add('hidden');
}

/**
 * Close the refresh cache modal
 */
function closeRefreshModal() {
  elements.refreshModal?.classList.add('hidden');
  elements.refreshStatus?.classList.add('hidden');
}

/**
 * Open the day detail modal
 */
function openDayDetailModal(button) {
  if (!button || !elements.dayDetailModal) return;
  const dayKey = button.dataset.dayKey;
  const summary = {
    key: dayKey,
    name: button.dataset.dayName,
    dateLabel: button.dataset.dayDate,
    summary: button.dataset.daySummary,
    high: parseNumber(button.dataset.dayHigh),
    low: parseNumber(button.dataset.dayLow),
    unit: button.dataset.dayUnit || '',
  };
  const details = dailyDetailsMap.get(dayKey);
  currentDayDetails = details || null;
  currentDayUnit = summary.unit || '';
  resetChartHover();

  if (elements.dayDetailTitle) {
    elements.dayDetailTitle.textContent = summary.name || 'Day Details';
  }
  if (elements.dayDetailSubtitle) {
    elements.dayDetailSubtitle.textContent = summary.dateLabel || '';
  }
  if (elements.dayDetailSummary) {
    elements.dayDetailSummary.textContent = summary.summary || '';
    if (summary.summary) {
      elements.dayDetailSummary.classList.remove('hidden');
    } else {
      elements.dayDetailSummary.classList.add('hidden');
    }
  }
  if (elements.dayDetailHighLow) {
    elements.dayDetailHighLow.textContent = formatHighLow(summary.high, summary.low, summary.unit);
  }

  if (!details || !details.hours || details.hours.length === 0) {
    if (elements.dayDetailCharts) {
      elements.dayDetailCharts.classList.add('hidden');
    }
    elements.dayDetailEmpty?.classList.remove('hidden');
    elements.dayDetailFeelsLike && (elements.dayDetailFeelsLike.textContent = '');
    elements.dayDetailTempRange && (elements.dayDetailTempRange.textContent = '');
    elements.dayDetailPrecipRange && (elements.dayDetailPrecipRange.textContent = '');
    elements.dayDetailTimeAxis && (elements.dayDetailTimeAxis.textContent = '');
  } else {
    elements.dayDetailEmpty?.classList.add('hidden');
    elements.dayDetailCharts?.classList.remove('hidden');
    renderDayCharts(details, summary.unit);
  }

  elements.dayDetailModal.classList.remove('hidden');
}

/**
 * Close the day detail modal
 */
function closeDayDetailModal() {
  elements.dayDetailModal?.classList.add('hidden');
  resetChartHover();
  currentDayDetails = null;
}

function parseNumber(value) {
  if (value === undefined || value === null || value === '') return null;
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}

function formatHighLow(high, low, unit) {
  const unitLabel = unit ? ` ${unit}` : '';
  if (high == null && low == null) return '';
  if (high != null && low != null) {
    return `High ${high}${unitLabel} / Low ${low}${unitLabel}`;
  }
  if (high != null) {
    return `High ${high}${unitLabel}`;
  }
  return `Low ${low}${unitLabel}`;
}

function renderDayCharts(details, unit) {
  const hours = details.hours || [];
  const temps = hours.map((hour) =>
    Number.isFinite(hour.temperature) ? hour.temperature : null
  );
  const feels = hours.map((hour) =>
    Number.isFinite(hour.feelsLike) ? hour.feelsLike : null
  );
  const precip = hours.map((hour) =>
    Number.isFinite(hour.precipChance) ? hour.precipChance : null
  );

  const tempRange = getRange(temps);
  const feelsRange = getRange(feels);
  const precipRange = getRange(precip);
  const detailUnit = unit || hours.find((hour) => hour.temperatureUnit)?.temperatureUnit || '';
  const unitLabel = detailUnit ? ` ${detailUnit}` : '';
  currentDayUnit = detailUnit;

  if (elements.dayDetailTempRange) {
    if (tempRange) {
      elements.dayDetailTempRange.textContent = `${tempRange.min}${unitLabel} - ${tempRange.max}${unitLabel}`;
    } else {
      elements.dayDetailTempRange.textContent = '';
    }
  }
  if (elements.dayDetailFeelsLike) {
    if (feelsRange) {
      elements.dayDetailFeelsLike.textContent = `Feels like ${feelsRange.min}${unitLabel} - ${feelsRange.max}${unitLabel}`;
    } else {
      elements.dayDetailFeelsLike.textContent = '';
    }
  }
  if (elements.dayDetailPrecipRange) {
    if (precipRange) {
      elements.dayDetailPrecipRange.textContent = `Peak ${Math.round(precipRange.max)}%`;
    } else {
      elements.dayDetailPrecipRange.textContent = '';
    }
  }

  renderLineChart(elements.dayDetailTempChart, [
    { values: temps, className: 'chart-line-temp' },
    { values: feels, className: 'chart-line-feels' },
  ]);
  renderBarChart(elements.dayDetailPrecipChart, precip);
  renderTimeAxis(elements.dayDetailTimeAxis, hours);
  resetChartHover();
}

function getRange(values) {
  const filtered = values.filter((value) => Number.isFinite(value));
  if (!filtered.length) return null;
  return {
    min: Math.min(...filtered),
    max: Math.max(...filtered),
  };
}

function clearSvg(svg) {
  if (!svg) return;
  while (svg.firstChild) {
    svg.removeChild(svg.firstChild);
  }
}

function renderLineChart(svg, series) {
  if (!svg) return;
  clearSvg(svg);
  const width = 240;
  const height = 80;
  svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
  svg.setAttribute('preserveAspectRatio', 'none');

  const allValues = series
    .flatMap((item) => item.values)
    .filter((value) => Number.isFinite(value));
  if (!allValues.length) return;

  const minValue = Math.min(...allValues);
  const maxValue = Math.max(...allValues);
  const range = maxValue - minValue || 1;
  const count = series[0]?.values?.length || 0;

  for (let i = 1; i < 4; i += 1) {
    const gridLine = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    const y = (height / 4) * i;
    gridLine.setAttribute('x1', '0');
    gridLine.setAttribute('x2', `${width}`);
    gridLine.setAttribute('y1', `${y}`);
    gridLine.setAttribute('y2', `${y}`);
    gridLine.setAttribute('class', 'chart-grid');
    svg.appendChild(gridLine);
  }

  series.forEach((item) => {
    const pathData = buildLinePath(item.values, count, width, height, minValue, range);
    if (!pathData) return;
    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path.setAttribute('d', pathData);
    path.setAttribute('class', item.className);
    svg.appendChild(path);
  });
}

function buildLinePath(values, count, width, height, minValue, range) {
  let path = '';
  let started = false;
  const total = count || values.length;
  for (let i = 0; i < values.length; i += 1) {
    const value = values[i];
    if (!Number.isFinite(value)) {
      started = false;
      continue;
    }
    const x = total <= 1 ? width / 2 : (i / (total - 1)) * width;
    const y = height - ((value - minValue) / range) * height;
    if (!started) {
      path += `M ${x} ${y}`;
      started = true;
    } else {
      path += ` L ${x} ${y}`;
    }
  }
  return path;
}

function renderBarChart(svg, values) {
  if (!svg) return;
  clearSvg(svg);
  const width = 240;
  const height = 80;
  svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
  svg.setAttribute('preserveAspectRatio', 'none');

  const count = values.length;
  if (!count) return;

  for (let i = 1; i < 4; i += 1) {
    const gridLine = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    const y = (height / 4) * i;
    gridLine.setAttribute('x1', '0');
    gridLine.setAttribute('x2', `${width}`);
    gridLine.setAttribute('y1', `${y}`);
    gridLine.setAttribute('y2', `${y}`);
    gridLine.setAttribute('class', 'chart-grid');
    svg.appendChild(gridLine);
  }

  const barWidth = width / count;
  const gap = 2;
  values.forEach((value, index) => {
    if (!Number.isFinite(value)) return;
    const clamped = Math.min(Math.max(value, 0), 100);
    const barHeight = (clamped / 100) * height;
    const x = index * barWidth + gap / 2;
    const y = height - barHeight;
    const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    rect.setAttribute('x', `${x}`);
    rect.setAttribute('y', `${y}`);
    rect.setAttribute('width', `${Math.max(barWidth - gap, 1)}`);
    rect.setAttribute('height', `${barHeight}`);
    rect.setAttribute('rx', '1.5');
    rect.setAttribute('class', 'chart-bar');
    svg.appendChild(rect);
  });
}

function renderTimeAxis(container, hours) {
  if (!container) return;
  container.innerHTML = '';
  if (!hours.length) return;
  const step = Math.max(1, Math.round(hours.length / 5));
  const labels = [];
  for (let i = 0; i < hours.length; i += step) {
    if (hours[i]?.time) {
      labels.push(hours[i].time);
    }
  }
  const lastLabel = hours[hours.length - 1]?.time;
  if (lastLabel && labels[labels.length - 1] !== lastLabel) {
    labels.push(lastLabel);
  }
  labels.forEach((label) => {
    const span = document.createElement('span');
    span.textContent = label;
    container.appendChild(span);
  });
}

function resetChartHover() {
  hideChartTooltip(elements.dayDetailTempTooltip, elements.dayDetailTempMarker);
  hideChartTooltip(elements.dayDetailPrecipTooltip, elements.dayDetailPrecipMarker);
}

function hideChartTooltip(tooltip, marker) {
  tooltip?.classList.add('hidden');
  marker?.classList.add('hidden');
}

function showChartTooltip(tooltip, marker, container, x, text) {
  if (!tooltip || !marker || !container) return;
  tooltip.textContent = text;
  tooltip.classList.remove('hidden');
  marker.classList.remove('hidden');

  const width = container.clientWidth || 1;
  const markerX = Math.max(0, Math.min(x, width));
  marker.style.left = `${markerX}px`;

  const tooltipWidth = tooltip.offsetWidth || 0;
  const halfWidth = tooltipWidth / 2;
  const minLeft = halfWidth + 8;
  const maxLeft = width - halfWidth - 8;
  const tooltipX = Math.max(minLeft, Math.min(markerX, maxLeft));
  tooltip.style.left = `${tooltipX}px`;
}

function getPointerEvent(event) {
  if (event.touches && event.touches[0]) {
    return event.touches[0];
  }
  if (event.changedTouches && event.changedTouches[0]) {
    return event.changedTouches[0];
  }
  return event;
}

function getHoverPosition(event, container, count) {
  const pointer = getPointerEvent(event);
  const rect = container.getBoundingClientRect();
  const width = rect.width || 1;
  const rawX = pointer.clientX - rect.left;
  const clampedX = Math.max(0, Math.min(rawX, width));
  if (!count) {
    return { index: 0, x: clampedX, width };
  }
  const ratio = width <= 1 ? 0 : clampedX / width;
  const index = Math.max(0, Math.min(count - 1, Math.round(ratio * (count - 1))));
  return { index, x: clampedX, width };
}

function formatTempValue(value, unit) {
  if (!Number.isFinite(value)) {
    return '--';
  }
  return unit ? `${value} ${unit}` : `${value}`;
}

function formatPrecipValue(value) {
  if (!Number.isFinite(value)) {
    return '--';
  }
  return `${Math.round(value)}%`;
}

function handleTempChartMove(event) {
  if (!currentDayDetails || !elements.dayDetailTempChart) return;
  const hours = currentDayDetails.hours || [];
  if (!hours.length) return;
  const container = elements.dayDetailTempChart.parentElement;
  if (!container) return;

  const position = getHoverPosition(event, container, hours.length);
  const hour = hours[position.index] || {};
  const unit = currentDayUnit || hour.temperatureUnit || '';
  const timeLabel = hour.time ? `${hour.time} ` : '';
  const tempText = formatTempValue(hour.temperature, unit);
  const feelsText = formatTempValue(hour.feelsLike, unit);
  const tooltipText = `${timeLabel}${tempText} / Feels ${feelsText}`;

  showChartTooltip(
    elements.dayDetailTempTooltip,
    elements.dayDetailTempMarker,
    container,
    position.x,
    tooltipText
  );
}

function handlePrecipChartMove(event) {
  if (!currentDayDetails || !elements.dayDetailPrecipChart) return;
  const hours = currentDayDetails.hours || [];
  if (!hours.length) return;
  const container = elements.dayDetailPrecipChart.parentElement;
  if (!container) return;

  const position = getHoverPosition(event, container, hours.length);
  const hour = hours[position.index] || {};
  const timeLabel = hour.time ? `${hour.time} ` : '';
  const precipText = formatPrecipValue(hour.precipChance);
  const tooltipText = `${timeLabel}${precipText} chance of precipitation`;

  showChartTooltip(
    elements.dayDetailPrecipTooltip,
    elements.dayDetailPrecipMarker,
    container,
    position.x,
    tooltipText
  );
}
/**
 * Handle refresh/delete actions for a location
 */
async function handleRefreshAction(action, locationKey) {
  if (!locationKey) return;
  const isDelete = action === 'delete';

  closeRefreshModal();
  if (elements.loadingText) {
    elements.loadingText.textContent = isDelete
      ? 'Removing cached data...'
      : 'Refreshing weather data...';
  }
  showState(elements.loadingState);

  try {
    const response = await fetch('/refresh', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action, location_key: locationKey }),
    });
    if (!response.ok) {
      throw new Error('Refresh failed');
    }
  } catch (error) {
    showState(elements.weatherState);
    openRefreshModal();
    if (elements.refreshStatus) {
      elements.refreshStatus.textContent = 'Unable to update cache. Please try again.';
      elements.refreshStatus.classList.remove('hidden');
    }
    return;
  }

  window.location.reload();
}

/**
 * Check if user has moved and offer to switch location
 */
function checkForLocationSwitch(coords) {
  const cached = getCachedLocation();
  if (!cached) return;
  
  const fresh = { lat: coords.latitude, lon: coords.longitude };
  if (isSignificantlyDifferent(cached, fresh)) {
    openSwitchModal(fresh);
  }
}

/**
 * Initialize the application
 */
function initWeatherApp(options = {}) {
  const { hasWeatherData, usedCachedLocation, hasLocationParams, dailyDetails } = options;
  if (Array.isArray(dailyDetails)) {
    dailyDetailsMap = new Map(dailyDetails.map((day) => [day.key, day]));
  }

  // Initial load logic
  if (!hasWeatherData && !hasLocationParams) {
    if (!navigator.geolocation) {
      showState(elements.permissionState);
      if (elements.permissionError) {
        elements.permissionError.textContent = 'Geolocation is not supported';
        elements.permissionError.classList.remove('hidden');
      }
    } else {
      requestLocation();
    }
  } else if (usedCachedLocation && navigator.geolocation) {
    requestLocation({ showLoading: false, onSuccess: checkForLocationSwitch });
  }

  // Event Listeners
  elements.grantLocationBtn?.addEventListener('click', () => {
    elements.permissionError?.classList.add('hidden');
    requestLocation();
  });

  elements.toggleLocationBtn?.addEventListener('click', openModal);
  elements.closeModalBtn?.addEventListener('click', closeModal);
  elements.modalBackdrop?.addEventListener('click', closeModal);

  document.addEventListener('keydown', (e) => {
    if (e.key !== 'Escape') return;
    if (!elements.locationModal?.classList.contains('hidden')) {
      closeModal();
    }
    if (!elements.switchLocationModal?.classList.contains('hidden')) {
      closeSwitchModal();
    }
    if (!elements.refreshModal?.classList.contains('hidden')) {
      closeRefreshModal();
    }
    if (!elements.dayDetailModal?.classList.contains('hidden')) {
      closeDayDetailModal();
    }
  });

  elements.useCurrentLocationBtn?.addEventListener('click', () => {
    closeModal();
    requestLocation();
  });

  elements.switchToCurrentBtn?.addEventListener('click', () => {
    if (!pendingSwitchLocation) return;
    const coords = pendingSwitchLocation;
    closeSwitchModal();
    redirectToLocation(coords);
  });

  elements.keepLocationBtn?.addEventListener('click', closeSwitchModal);
  elements.switchModalBackdrop?.addEventListener('click', closeSwitchModal);

  elements.refreshBtn?.addEventListener('click', openRefreshModal);
  elements.refreshModalBackdrop?.addEventListener('click', closeRefreshModal);
  elements.refreshCloseBtn?.addEventListener('click', closeRefreshModal);
  elements.dayDetailBackdrop?.addEventListener('click', closeDayDetailModal);
  elements.dayDetailCloseBtn?.addEventListener('click', closeDayDetailModal);

  elements.refreshLocationList?.addEventListener('click', (event) => {
    const button = event.target.closest('button[data-refresh-action]');
    if (!button) return;
    const action = button.dataset.refreshAction;
    const locationKey = button.dataset.locationKey;
    handleRefreshAction(action, locationKey);
  });

  elements.dailyForecastList?.addEventListener('click', (event) => {
    const button = event.target.closest('button[data-day-key]');
    if (!button) return;
    openDayDetailModal(button);
  });

  const tempContainer = elements.dayDetailTempChart?.parentElement;
  const precipContainer = elements.dayDetailPrecipChart?.parentElement;

  tempContainer?.addEventListener('mousemove', handleTempChartMove);
  tempContainer?.addEventListener('mouseleave', () => {
    hideChartTooltip(elements.dayDetailTempTooltip, elements.dayDetailTempMarker);
  });

  precipContainer?.addEventListener('mousemove', handlePrecipChartMove);
  precipContainer?.addEventListener('mouseleave', () => {
    hideChartTooltip(elements.dayDetailPrecipTooltip, elements.dayDetailPrecipMarker);
  });
}

/**
 * Determine weather theme based on forecast text
 */
function getWeatherTheme(shortForecast, isDaytime = true) {
  if (!shortForecast) return null;
  
  const forecast = shortForecast.toLowerCase();
  
  // Check for specific weather conditions (order matters - more specific first)
  if (forecast.includes('thunder') || forecast.includes('storm')) {
    return 'storm';
  }
  if (forecast.includes('snow') || forecast.includes('blizzard') || forecast.includes('flurr')) {
    return 'snow';
  }
  if (forecast.includes('rain') || forecast.includes('shower') || forecast.includes('drizzle')) {
    return 'rain';
  }
  if (forecast.includes('fog') || forecast.includes('mist') || forecast.includes('haze') || forecast.includes('smoke')) {
    return 'fog';
  }
  if (forecast.includes('wind') && !forecast.includes('sun') && !forecast.includes('clear')) {
    return 'wind';
  }
  if (forecast.includes('cloud') || forecast.includes('overcast')) {
    return 'cloudy';
  }
  if (forecast.includes('hot') || forecast.includes('heat')) {
    return 'hot';
  }
  if (forecast.includes('sun') || forecast.includes('clear') || forecast.includes('fair')) {
    return isDaytime ? 'clear' : 'night';
  }
  
  // Default based on time of day
  return isDaytime ? null : 'night';
}

/**
 * Create weather animation particles
 */
function createWeatherEffects(theme) {
  const container = document.getElementById('weather-effects');
  if (!container) return;
  
  // Clear existing effects
  container.innerHTML = '';
  
  // Check for reduced motion preference
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    return;
  }
  
  switch (theme) {
    case 'rain':
    case 'storm':
      createRainEffect(container, theme === 'storm');
      break;
    case 'snow':
      createSnowEffect(container);
      break;
    case 'fog':
      createFogEffect(container);
      break;
    case 'clear':
      createSunEffect(container);
      break;
    case 'night':
      createStarsEffect(container);
      break;
    case 'wind':
      createWindEffect(container);
      break;
    case 'hot':
      createHeatEffect(container);
      break;
  }
}

function createRainEffect(container, isStorm) {
  const dropCount = isStorm ? 120 : 80;
  
  for (let i = 0; i < dropCount; i++) {
    const drop = document.createElement('div');
    drop.className = 'weather-particle rain-drop';
    drop.style.left = `${Math.random() * 100}%`;
    drop.style.animationDuration = `${0.4 + Math.random() * 0.4}s`;
    drop.style.animationDelay = `${Math.random() * 2}s`;
    drop.style.opacity = 0.5 + Math.random() * 0.5;
    // Vary the height for depth perception
    const scale = 0.5 + Math.random() * 0.5;
    drop.style.transform = `scaleY(${scale})`;
    container.appendChild(drop);
  }
  
  // Add rain mist at the bottom
  const mist = document.createElement('div');
  mist.className = 'weather-particle rain-mist';
  container.appendChild(mist);
  
  if (isStorm) {
    // Add multiple lightning flashes with different timings
    for (let i = 0; i < 2; i++) {
      const flash = document.createElement('div');
      flash.className = 'lightning-flash';
      flash.style.animationDelay = `${i * 3 + Math.random() * 2}s`;
      container.appendChild(flash);
    }
  }
}

function createSnowEffect(container) {
  const flakeCount = 40;
  
  for (let i = 0; i < flakeCount; i++) {
    const flake = document.createElement('div');
    flake.className = 'weather-particle snowflake';
    flake.style.left = `${Math.random() * 100}%`;
    flake.style.width = `${4 + Math.random() * 6}px`;
    flake.style.height = flake.style.width;
    flake.style.animationDuration = `${5 + Math.random() * 10}s`;
    flake.style.animationDelay = `${Math.random() * 5}s`;
    flake.style.opacity = 0.4 + Math.random() * 0.4;
    container.appendChild(flake);
  }
}

function createFogEffect(container) {
  for (let i = 0; i < 3; i++) {
    const fog = document.createElement('div');
    fog.className = 'weather-particle fog-layer';
    container.appendChild(fog);
  }
}

function createSunEffect(container) {
  // Add sun glow
  const glow = document.createElement('div');
  glow.className = 'weather-particle sun-glow';
  container.appendChild(glow);
  
  // Add sun rays
  for (let i = 0; i < 3; i++) {
    const ray = document.createElement('div');
    ray.className = 'weather-particle sun-ray';
    container.appendChild(ray);
  }
}

function createStarsEffect(container) {
  // Add moon glow
  const moon = document.createElement('div');
  moon.className = 'weather-particle moon-glow';
  container.appendChild(moon);
  
  // Regular stars
  const starCount = 80;
  for (let i = 0; i < starCount; i++) {
    const star = document.createElement('div');
    star.className = 'weather-particle star';
    // Make some stars brighter
    if (Math.random() > 0.85) {
      star.classList.add('bright');
    }
    star.style.left = `${Math.random() * 100}%`;
    star.style.top = `${Math.random() * 70}%`;
    star.style.animationDuration = `${2 + Math.random() * 4}s`;
    star.style.animationDelay = `${Math.random() * 4}s`;
    container.appendChild(star);
  }
  
  // Shooting stars
  for (let i = 0; i < 3; i++) {
    const shootingStar = document.createElement('div');
    shootingStar.className = 'weather-particle shooting-star';
    shootingStar.style.left = `${20 + Math.random() * 40}%`;
    shootingStar.style.top = `${5 + Math.random() * 20}%`;
    shootingStar.style.animationDelay = `${i * 4 + Math.random() * 3}s`;
    shootingStar.style.animationDuration = `${2.5 + Math.random() * 1.5}s`;
    container.appendChild(shootingStar);
  }
}

function createWindEffect(container) {
  const streakCount = 15;
  
  for (let i = 0; i < streakCount; i++) {
    const streak = document.createElement('div');
    streak.className = 'weather-particle wind-streak';
    streak.style.top = `${10 + Math.random() * 80}%`;
    streak.style.width = `${50 + Math.random() * 150}px`;
    streak.style.animationDuration = `${1 + Math.random() * 2}s`;
    streak.style.animationDelay = `${Math.random() * 3}s`;
    container.appendChild(streak);
  }
}

function createHeatEffect(container) {
  const wave = document.createElement('div');
  wave.className = 'weather-particle heat-wave';
  container.appendChild(wave);
}

/**
 * Apply weather-based background theme
 */
function applyWeatherTheme(shortForecast, isDaytime = true) {
  const theme = getWeatherTheme(shortForecast, isDaytime);
  if (theme) {
    document.body.setAttribute('data-weather', theme);
    createWeatherEffects(theme);
  } else {
    document.body.removeAttribute('data-weather');
    const container = document.getElementById('weather-effects');
    if (container) container.innerHTML = '';
  }
}

// Export for use in templates
window.WeatherApp = {
  init: initWeatherApp,
  showState,
  openModal,
  closeModal,
  requestLocation,
  applyWeatherTheme,
  getWeatherTheme,
};
