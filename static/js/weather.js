/**
 * Weather App - Location & UI Management
 */

// DOM Elements
const elements = {
  loadingState: document.getElementById('loading-state'),
  permissionState: document.getElementById('permission-state'),
  weatherState: document.getElementById('weather-state'),
  loadingText: document.getElementById('loading-text'),
  loadingActions: document.getElementById('loading-actions'),
  loadingSearchBtn: document.getElementById('loading-search'),
  grantLocationBtn: document.getElementById('grant-location'),
  permissionError: document.getElementById('permission-error'),
  permissionSearchBtn: document.getElementById('search-location'),
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
  locationForm: document.getElementById('location-form'),
  locationSuggestions: document.getElementById('location-suggestions'),
  locationStatus: document.getElementById('location-status'),
  refreshBtn: document.getElementById('refresh-weather'),
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
  hourlyCurrentTime: document.getElementById('hourly-current-time'),
  hourlyContent: document.getElementById('hourly-content'),
  alertsContainer: document.getElementById('alerts-container'),
  advisoryBadge: document.getElementById('advisory-badge'),
};

// Configuration
const CONFIG = {
  LOCATION_DELTA_THRESHOLD: 0.03,
  AUTO_REFRESH_MS: 5 * 60 * 1000,
  GEOLOCATION_QUICK: {
    label: 'Checking for a recent location...',
    options: {
      enableHighAccuracy: false,
      timeout: 8000,
      maximumAge: 600000,
    },
  },
  GEOLOCATION_FRESH: {
    label: 'Getting a fresh GPS fix...',
    options: {
      enableHighAccuracy: true,
      timeout: 20000,
      maximumAge: 0,
    },
  },
};

const ALERT_RADIUS_COOKIE = 'alert_radius_mi';
const ALERT_RADIUS_DEFAULT = 10;
const ALERT_RADIUS_OPTIONS = [5, 10, 15, 20, 25, 30, 40, 50, 75, 100];

// State
let pendingSwitchLocation = null;
let locationRequestId = 0;
let currentLocationKey = null;
let dailyDetailsMap = new Map();
let currentDayDetails = null;
let currentDayUnit = '';
let currentTimeZone = null;

/**
 * Show a specific UI state and hide others
 */
function showState(state) {
  elements.loadingState?.classList.add('hidden');
  elements.permissionState?.classList.add('hidden');
  elements.weatherState?.classList.add('hidden');
  state?.classList.remove('hidden');
}

function setLoadingText(message) {
  if (elements.loadingText && message) {
    elements.loadingText.textContent = message;
  }
}

function setLoadingActionsVisible(visible) {
  if (!elements.loadingActions) return;
  elements.loadingActions.classList.toggle('hidden', !visible);
}

function showLoading(message, { showLocationActions = false } = {}) {
  setLoadingText(message);
  setLoadingActionsVisible(showLocationActions);
  showState(elements.loadingState);
}

function resetPermissionUI() {
  if (elements.permissionError) {
    elements.permissionError.textContent = '';
    elements.permissionError.classList.add('hidden');
  }
  if (elements.grantLocationBtn) {
    elements.grantLocationBtn.textContent = 'Enable Location';
  }
}

function showPermissionPrompt() {
  resetPermissionUI();
  showState(elements.permissionState);
}

function showPermissionError(message) {
  resetPermissionUI();
  if (elements.permissionError && message) {
    elements.permissionError.textContent = message;
    elements.permissionError.classList.remove('hidden');
  }
  if (elements.grantLocationBtn) {
    elements.grantLocationBtn.textContent = 'Try Again';
  }
  showState(elements.permissionState);
}

function cancelLocationRequest() {
  locationRequestId += 1;
}

/**
 * Open the location search modal
 */
function openModal() {
  elements.locationModal?.classList.remove('hidden');
  setLocationStatus('');
  elements.addressInput?.focus();
}

function openManualSearch() {
  cancelLocationRequest();
  setLoadingActionsVisible(false);
  elements.loadingState?.classList.add('hidden');
  elements.permissionState?.classList.add('hidden');
  openModal();
}

/**
 * Close the location search modal
 */
function closeModal() {
  elements.locationModal?.classList.add('hidden');
  setLocationStatus('');
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

function setCookieValue(name, value, days = 30) {
  const maxAge = days * 24 * 60 * 60;
  document.cookie = `${name}=${encodeURIComponent(value)}; max-age=${maxAge}; path=/; samesite=lax`;
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

function parseAlertRadius(value) {
  const parsed = Number.parseInt(value, 10);
  if (!Number.isFinite(parsed)) return null;
  return ALERT_RADIUS_OPTIONS.includes(parsed) ? parsed : null;
}

function getAlertRadiusPreference() {
  const stored = parseAlertRadius(getCookieValue(ALERT_RADIUS_COOKIE));
  return stored ?? ALERT_RADIUS_DEFAULT;
}

function setAlertRadiusPreference(value) {
  if (!ALERT_RADIUS_OPTIONS.includes(value)) return;
  setCookieValue(ALERT_RADIUS_COOKIE, value);
}

function applyAlertAreaFilter(container, radius) {
  const areaTags = Array.from(container.querySelectorAll('.alert-modern__area-tag'));
  let visibleCount = 0;
  areaTags.forEach((tag) => {
    const distance = Number.parseFloat(tag.dataset.distanceMi);
    const isVisible = Number.isFinite(distance) ? distance <= radius : true;
    tag.classList.toggle('is-hidden', !isVisible);
    if (isVisible) {
      visibleCount += 1;
    }
  });

  const radiusLabel = container.querySelector('[data-alert-radius-label]');
  if (radiusLabel) {
    radiusLabel.textContent = radius;
  }

  const countLabel = container.querySelector('[data-alert-count-label]');
  if (countLabel) {
    countLabel.textContent = `${visibleCount} ${visibleCount === 1 ? 'county' : 'counties'}`;
  }
}

function updateAlertAreaControls(radius) {
  document.querySelectorAll('[data-alert-radius]').forEach((button) => {
    const value = parseAlertRadius(button.dataset.alertRadius);
    const isActive = value === radius;
    button.classList.toggle('is-active', isActive);
    button.setAttribute('aria-pressed', isActive ? 'true' : 'false');
  });
}

function initAlertAreaFilters() {
  const containers = document.querySelectorAll('[data-alert-areas]');
  if (!containers.length) return;

  const applyAll = (radius) => {
    containers.forEach((container) => applyAlertAreaFilter(container, radius));
    updateAlertAreaControls(radius);
  };

  const initialRadius = getAlertRadiusPreference();
  applyAll(initialRadius);

  containers.forEach((container) => {
    container.querySelectorAll('[data-alert-radius]').forEach((button) => {
      button.addEventListener('click', () => {
        const selected = parseAlertRadius(button.dataset.alertRadius);
        if (!selected) return;
        setAlertRadiusPreference(selected);
        applyAll(selected);
      });
    });
  });
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
function requestLocation({ showLoading: shouldShowLoading = true, onSuccess } = {}) {
  if (!navigator.geolocation) {
    if (shouldShowLoading) {
      showPermissionError('Geolocation is not supported in this browser.');
    }
    return;
  }

  locationRequestId += 1;
  const requestId = locationRequestId;
  const handleSuccess = onSuccess || ((coords) => redirectToLocation(coords));
  const attempts = shouldShowLoading
    ? [CONFIG.GEOLOCATION_QUICK, CONFIG.GEOLOCATION_FRESH]
    : [CONFIG.GEOLOCATION_QUICK];

  if (shouldShowLoading) {
    resetPermissionUI();
    showLoading(attempts[0].label, { showLocationActions: true });
  }

  const runAttempt = (index) => {
    const attempt = attempts[index];
    if (shouldShowLoading && attempt?.label) {
      setLoadingText(attempt.label);
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        if (requestId !== locationRequestId) return;
        if (shouldShowLoading) {
          setLoadingText('Loading weather...');
        }
        handleSuccess(position.coords);
      },
      (error) => {
        if (requestId !== locationRequestId) return;
        if (!shouldShowLoading) return;

        if (error.code === error.PERMISSION_DENIED) {
          showPermissionError(
            'Location permission was denied. Enable it in your browser settings to use current location.'
          );
          return;
        }

        const shouldRetry =
          (error.code === error.TIMEOUT || error.code === error.POSITION_UNAVAILABLE) &&
          index + 1 < attempts.length;
        if (shouldRetry) {
          runAttempt(index + 1);
          return;
        }

        let message = error.message || 'Unable to get location.';
        if (error.code === error.TIMEOUT) {
          message =
            'Location is taking longer than expected. Turn on location and try again, or search manually.';
        } else if (error.code === error.POSITION_UNAVAILABLE) {
          message = 'Location is unavailable. Check device location settings and try again.';
        }
        showPermissionError(message);
      },
      attempt?.options
    );
  };

  runAttempt(0);
}

function initLocationAccess() {
  if (!navigator.geolocation) {
    showPermissionError('Geolocation is not supported in this browser.');
    return;
  }

  if (!navigator.permissions?.query) {
    requestLocation();
    return;
  }

  navigator.permissions
    .query({ name: 'geolocation' })
    .then((status) => {
      if (status.state === 'granted') {
        requestLocation();
      } else if (status.state === 'denied') {
        showPermissionError(
          'Location permission is blocked. Enable it in your browser settings to use current location.'
        );
      } else {
        showPermissionPrompt();
      }
    })
    .catch(() => {
      requestLocation();
    });
}

function setLocationStatus(message) {
  if (!elements.locationStatus) return;
  if (!message) {
    elements.locationStatus.textContent = '';
    elements.locationStatus.classList.add('hidden');
    return;
  }
  elements.locationStatus.textContent = message;
  elements.locationStatus.classList.remove('hidden');
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

function updateAlertValidityBars(now = new Date()) {
  const bars = document.querySelectorAll('.alert-validity__bar');
  if (!bars.length) return;
  const nowTime = now instanceof Date ? now.getTime() : new Date(now).getTime();
  if (!Number.isFinite(nowTime)) return;
  bars.forEach((bar) => {
    const startValue = bar.dataset.alertStart;
    const endValue = bar.dataset.alertEnd;
    if (!startValue || !endValue) return;
    const startTime = Date.parse(startValue);
    const endTime = Date.parse(endValue);
    if (!Number.isFinite(startTime) || !Number.isFinite(endTime) || endTime <= startTime) {
      bar.style.setProperty('--alert-progress', '0%');
      return;
    }
    const ratio = (nowTime - startTime) / (endTime - startTime);
    const clamped = Math.max(0, Math.min(1, ratio));
    bar.style.setProperty('--alert-progress', `${(clamped * 100).toFixed(2)}%`);
  });
}

function formatDateTimeLabel(value, timeZone) {
  const date = value instanceof Date ? value : new Date(value);
  if (!Number.isFinite(date.getTime())) return '';
  const options = {
    weekday: 'short',
    month: '2-digit',
    day: '2-digit',
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  };
  if (timeZone) {
    options.timeZone = timeZone;
  }
  let parts;
  try {
    parts = new Intl.DateTimeFormat('en-US', options).formatToParts(date);
  } catch (error) {
    delete options.timeZone;
    try {
      parts = new Intl.DateTimeFormat('en-US', options).formatToParts(date);
    } catch (fallbackError) {
      return '';
    }
  }
  const byType = {};
  parts.forEach((part) => {
    if (part.type !== 'literal') {
      byType[part.type] = part.value;
    }
  });
  const weekday = byType.weekday || '';
  const month = byType.month || '';
  const day = byType.day || '';
  const hour = byType.hour || '';
  const minute = byType.minute || '';
  const dayPeriod = (byType.dayPeriod || '').toLowerCase();
  if (!weekday || !month || !day || !hour || !minute || !dayPeriod) {
    return '';
  }
  return `${weekday}, ${month}/${day}, ${hour}:${minute}${dayPeriod}`;
}

function formatTimeLabelWithSeconds(value, timeZone) {
  const date = value instanceof Date ? value : new Date(value);
  if (!Number.isFinite(date.getTime())) return '';
  const options = {
    weekday: 'short',
    month: '2-digit',
    day: '2-digit',
    hour: 'numeric',
    minute: '2-digit',
    second: '2-digit',
    hour12: true,
  };
  if (timeZone) {
    options.timeZone = timeZone;
  }
  let parts;
  try {
    parts = new Intl.DateTimeFormat('en-US', options).formatToParts(date);
  } catch (error) {
    delete options.timeZone;
    try {
      parts = new Intl.DateTimeFormat('en-US', options).formatToParts(date);
    } catch (fallbackError) {
      return '';
    }
  }
  const byType = {};
  parts.forEach((part) => {
    if (part.type !== 'literal') {
      byType[part.type] = part.value;
    }
  });
  const weekday = byType.weekday || '';
  const month = byType.month || '';
  const day = byType.day || '';
  const hour = byType.hour || '';
  const minute = byType.minute || '';
  const second = byType.second || '';
  const dayPeriod = (byType.dayPeriod || '').toLowerCase();
  if (!weekday || !month || !day || !hour || !minute || !second || !dayPeriod) {
    return '';
  }
  return `${weekday} ${month}/${day} ${hour}:${minute}:${second} ${dayPeriod}`;
}

function updateDateTime() {
  const now = new Date();
  const target = document.getElementById('datetime');
  const label = formatDateTimeLabel(now, currentTimeZone);
  const shouldUpdateLabel = target?.dataset?.datetimeMode === 'current';
  if (target && label && shouldUpdateLabel) {
    target.textContent = label;
  }
  updateAlertValidityBars(now);
  updateHeaderTimestamp();
}

function normalizeHeaderLabel(value) {
  if (typeof value !== 'string') return '';
  return value.replace(/^(as of|forecast for|observed)\s+/i, '').trim();
}

function formatRelativeAge(value) {
  const timestamp = typeof value === 'string' ? Date.parse(value) : Number.NaN;
  if (!Number.isFinite(timestamp)) return '';
  const diffMs = Date.now() - timestamp;
  if (!Number.isFinite(diffMs) || diffMs < 0) return '';
  const minutes = Math.max(1, Math.floor(diffMs / 60000));
  if (minutes < 60) {
    return `${minutes}m ago`;
  }
  const hours = Math.floor(minutes / 60);
  const remainingMinutes = minutes % 60;
  if (hours < 24) {
    return remainingMinutes ? `${hours}h ${remainingMinutes}m ago` : `${hours}h ago`;
  }
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

function updateHeaderTimestamp({ observationLabel, observationStation, observationTimestamp } = {}) {
  const target = document.getElementById('datetime');
  if (!target || target.dataset?.datetimeMode !== 'forecast') return;

  if (typeof observationLabel === 'string') {
    target.dataset.observationLabel = normalizeHeaderLabel(observationLabel);
  }
  if (typeof observationStation === 'string') {
    target.dataset.observationStation = observationStation.trim();
  }
  if (typeof observationTimestamp === 'string') {
    target.dataset.observationTimestamp = observationTimestamp.trim();
  }

  const observationText = normalizeHeaderLabel(target.dataset.observationLabel || '');
  const stationText = (target.dataset.observationStation || '').trim();
  const ageText = formatRelativeAge(target.dataset.observationTimestamp || '');
  if (!observationText) return;

  target.textContent = stationText
    ? `Observed ${observationText} - ${stationText}${ageText ? ` \u00b7 ${ageText}` : ''}`
    : `Observed ${observationText}${ageText ? ` \u00b7 ${ageText}` : ''}`;
}

function updateHourlyClock() {
  const target = elements.hourlyCurrentTime;
  if (!target) return;
  const now = new Date();
  const label = formatTimeLabelWithSeconds(now, currentTimeZone);
  if (label) {
    target.textContent = label;
  }
}

function startDateTimeTicker() {
  updateDateTime();
  updateHourlyClock();
  window.setInterval(updateDateTime, 60000);
  window.setInterval(updateHourlyClock, 1000);
}

function startAutoRefresh(hasWeatherData) {
  if (!hasWeatherData) return;
  window.setTimeout(() => {
    refreshCurrentLocation({ showLoading: false });
  }, CONFIG.AUTO_REFRESH_MS);
}

function updateTextTargets(selector, value) {
  document.querySelectorAll(selector).forEach((element) => {
    element.textContent = value;
  });
}

function normalizeNumber(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return null;
  return Math.round(number);
}

function updateInlineValue(selector, value) {
  const text = value == null ? '--' : `${value}`;
  updateTextTargets(selector, text);
}

function updateStatValue(selector, value, suffix = '') {
  const text = value == null ? '--' : `${value}${suffix}`;
  updateTextTargets(selector, text);
}

function updateHumidity(value) {
  const normalized = normalizeNumber(value);
  updateInlineValue('[data-humidity-value]', normalized);
  updateStatValue('[data-humidity-stat]', normalized, '%');
}

function updatePrecip(value) {
  const normalized = normalizeNumber(value);
  updateInlineValue('[data-precip-value]', normalized);
  updateStatValue('[data-precip-stat]', normalized, '%');
}

function updateFeelsLike(value) {
  const normalized = normalizeNumber(value);
  const text = normalized == null ? '--' : `${normalized}\u00b0`;
  updateTextTargets('[data-feels-like-temp]', text);
}

function updateActualTemp(value, unit) {
  const normalized = normalizeNumber(value);
  const unitLabel = unit ? `${unit}` : '';
  const text = normalized == null ? 'Actual --' : `Actual ${normalized}\u00b0${unitLabel}`;
  updateTextTargets('[data-actual-temp]', text);
}

function updateAdvisoryBadge(hasAdvisory) {
  if (!elements.advisoryBadge) return;
  elements.advisoryBadge.classList.toggle('hidden', !hasAdvisory);
}

function updateDailyDetails(details) {
  if (!Array.isArray(details)) return;
  dailyDetailsMap = new Map(details.map((day) => [day.key, day]));
  if (!currentDayDetails?.key) return;
  const updated = dailyDetailsMap.get(currentDayDetails.key);
  if (!updated) return;
  currentDayDetails = updated;
  if (elements.dayDetailModal && !elements.dayDetailModal.classList.contains('hidden')) {
    renderDayCharts(updated, currentDayUnit);
  }
}

function updateHourlyContent(hourlyToday, hourlyError) {
  if (!elements.hourlyContent) return;
  elements.hourlyContent.textContent = '';

  if (Array.isArray(hourlyToday) && hourlyToday.length) {
    const list = document.createElement('div');
    list.className = 'hourly-list';
    hourlyToday.forEach((hour) => {
      const row = document.createElement('div');
      row.className = 'hour-row';

      const time = document.createElement('div');
      time.className = 'hour-time';
      time.textContent = hour?.time || '';

      const temp = document.createElement('div');
      temp.className = 'hour-temp';
      temp.textContent = Number.isFinite(hour?.temperature)
        ? `${hour.temperature}\u00b0`
        : '--';

      row.appendChild(time);
      row.appendChild(temp);

      if (hour?.shortForecast) {
        const summary = document.createElement('div');
        summary.className = 'hour-summary';
        summary.textContent = hour.shortForecast;
        row.appendChild(summary);
      }

      list.appendChild(row);
    });
    elements.hourlyContent.appendChild(list);
    return;
  }

  const panel = document.createElement('div');
  panel.className = 'glass-panel-subtle rounded-xl p-3 text-center';
  const message = document.createElement('p');
  message.className = 'text-white/60';
  message.textContent = hourlyError || 'Hourly forecast unavailable';
  panel.appendChild(message);
  elements.hourlyContent.appendChild(panel);
}

function updateAlertsContent(html) {
  if (!elements.alertsContainer) return;
  elements.alertsContainer.innerHTML = html || '';
  initAlertAreaFilters();
  updateAlertValidityBars(new Date());
}

function applyDeferredExtras(data) {
  if (!data || typeof data !== 'object') return;
  if (typeof data.location_key === 'string') {
    const trimmedKey = data.location_key.trim();
    if (trimmedKey) {
      currentLocationKey = trimmedKey;
    }
  }
  if (data.time_zone && typeof data.time_zone === 'string') {
    const trimmed = data.time_zone.trim();
    if (trimmed) {
      currentTimeZone = trimmed;
      updateDateTime();
      updateHourlyClock();
    }
  }
  if (
    typeof data.observation_label === 'string' ||
    typeof data.observation_station === 'string' ||
    typeof data.observation_timestamp === 'string'
  ) {
    updateHeaderTimestamp({
      observationLabel: data.observation_label,
      observationStation: data.observation_station,
      observationTimestamp: data.observation_timestamp,
    });
  }
  updateDailyDetails(data.daily_details);
  updateHourlyContent(data.hourly_today, data.hourly_error);
  if (typeof data.alerts_html === 'string') {
    updateAlertsContent(data.alerts_html);
  }
  updateHumidity(data.humidity);
  updatePrecip(data.precip_chance);
  updateFeelsLike(data.feels_like_temperature);
  updateActualTemp(data.actual_temperature, data.actual_temperature_unit || data.feels_like_unit);
  updateAdvisoryBadge(Boolean(data.alerts_has_advisory));
}

async function loadDeferredExtras(coords) {
  const latValue = Number(coords?.lat ?? coords?.latitude);
  const lonValue = Number(coords?.lon ?? coords?.longitude);
  if (!Number.isFinite(latValue) || !Number.isFinite(lonValue)) return;

  const params = new URLSearchParams({
    lat: latValue.toFixed(4),
    lon: lonValue.toFixed(4),
  });
  if (currentLocationKey) {
    params.set('location_key', currentLocationKey);
  }

  try {
    const response = await fetch(`/api/extras?${params.toString()}`, {
      headers: { Accept: 'application/json' },
    });
    if (!response.ok) return;
    const data = await response.json();
    applyDeferredExtras(data);
  } catch (error) {
    // Ignore deferred extras failures.
  }
}

function scheduleDeferredExtras(coords) {
  const run = () => loadDeferredExtras(coords);
  if ('requestIdleCallback' in window) {
    window.requestIdleCallback(run, { timeout: 2500 });
  } else {
    window.setTimeout(run, 0);
  }
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
 * Post a cache action for a location
 */
async function sendLocationCacheAction(action, locationKey) {
  if (!locationKey) return false;
  try {
    const response = await fetch('/refresh', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action, location_key: locationKey }),
    });
    return response.ok;
  } catch (error) {
    return false;
  }
}

/**
 * Refresh the currently displayed location
 */
async function refreshCurrentLocation({ showLoading: shouldShowLoading = false } = {}) {
  if (shouldShowLoading) {
    showLoading('Refreshing current location...');
  }
  if (currentLocationKey) {
    await sendLocationCacheAction('refresh', currentLocationKey);
  }
  window.location.reload();
}

/**
 * Delete a saved location from the location modal
 */
async function handleLocationDelete(locationKey) {
  if (!locationKey) return;
  closeModal();
  showLoading('Removing saved location...');

  const success = await sendLocationCacheAction('delete', locationKey);
  if (!success) {
    showState(elements.weatherState);
    openModal();
    setLocationStatus('Unable to update locations. Please try again.');
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
  const {
    hasWeatherData,
    hasLocationParams,
    dailyDetails,
    currentLocationKey: initialLocationKey,
    timeZone,
    deferExtras,
    coords,
  } = options;
  currentLocationKey = initialLocationKey || null;
  if (typeof timeZone === 'string') {
    const trimmed = timeZone.trim();
    currentTimeZone = trimmed ? trimmed : null;
  } else {
    currentTimeZone = null;
  }
  if (Array.isArray(dailyDetails)) {
    dailyDetailsMap = new Map(dailyDetails.map((day) => [day.key, day]));
  }

  startDateTimeTicker();
  startAutoRefresh(hasWeatherData);
  initAlertAreaFilters();
  if (hasWeatherData && deferExtras && coords) {
    scheduleDeferredExtras(coords);
  }
  updateHeaderTimestamp();

  // Initial load logic
  if (!hasWeatherData && !hasLocationParams) {
    initLocationAccess();
  }

  // Event Listeners
  elements.grantLocationBtn?.addEventListener('click', () => {
    resetPermissionUI();
    requestLocation();
  });
  elements.permissionSearchBtn?.addEventListener('click', openManualSearch);
  elements.loadingSearchBtn?.addEventListener('click', openManualSearch);

  elements.toggleLocationBtn?.addEventListener('click', openModal);
  elements.closeModalBtn?.addEventListener('click', closeModal);
  elements.modalBackdrop?.addEventListener('click', closeModal);
  elements.locationForm?.addEventListener('submit', () => {
    closeModal();
    const value = elements.addressInput?.value?.trim();
    showLoading(value ? 'Searching location...' : 'Loading weather...');
  });

  document.addEventListener('keydown', (e) => {
    if (e.key !== 'Escape') return;
    if (!elements.locationModal?.classList.contains('hidden')) {
      closeModal();
    }
    if (!elements.switchLocationModal?.classList.contains('hidden')) {
      closeSwitchModal();
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
    showLoading('Switching to current location...');
    redirectToLocation(coords);
  });

  elements.keepLocationBtn?.addEventListener('click', closeSwitchModal);
  elements.switchModalBackdrop?.addEventListener('click', closeSwitchModal);

  elements.refreshBtn?.addEventListener('click', () => {
    refreshCurrentLocation();
  });
  elements.dayDetailBackdrop?.addEventListener('click', closeDayDetailModal);
  elements.dayDetailCloseBtn?.addEventListener('click', closeDayDetailModal);

  elements.dailyForecastList?.addEventListener('click', (event) => {
    const button = event.target.closest('button[data-day-key]');
    if (!button) return;
    openDayDetailModal(button);
  });

  elements.locationSuggestions?.addEventListener('click', (event) => {
    const actionButton = event.target.closest('[data-location-action]');
    if (!actionButton) return;
    const action = actionButton.dataset.locationAction;
    if (action === 'delete') {
      handleLocationDelete(actionButton.dataset.locationKey);
      return;
    }
    if (action === 'select') {
      const lat = Number(actionButton.dataset.locationLat);
      const lon = Number(actionButton.dataset.locationLon);
      if (!Number.isFinite(lat) || !Number.isFinite(lon)) return;
      closeModal();
      const label = actionButton.dataset.locationLabel;
      showLoading(label ? `Switching to ${label}...` : 'Switching location...');
      redirectToLocation({ lat, lon });
    }
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
  const dropCount = isStorm ? 60 : 40;
  
  for (let i = 0; i < dropCount; i++) {
    const drop = document.createElement('div');
    drop.className = 'weather-particle rain-drop';
    drop.style.left = `${Math.random() * 100}%`;
    drop.style.animationDuration = `${0.5 + Math.random() * 0.5}s`;
    drop.style.animationDelay = `${Math.random() * 3}s`;
    drop.style.opacity = 0.3 + Math.random() * 0.4;
    container.appendChild(drop);
  }
  
  // Add rain mist at the bottom
  const mist = document.createElement('div');
  mist.className = 'weather-particle rain-mist';
  container.appendChild(mist);
  
  if (isStorm) {
    // Add lightning flash
    const flash = document.createElement('div');
    flash.className = 'lightning-flash';
    flash.style.animationDelay = `${Math.random() * 3}s`;
    container.appendChild(flash);
  }
}

function createSnowEffect(container) {
  const flakeCount = 25;
  
  for (let i = 0; i < flakeCount; i++) {
    const flake = document.createElement('div');
    flake.className = 'weather-particle snowflake';
    flake.style.left = `${Math.random() * 100}%`;
    flake.style.width = `${3 + Math.random() * 5}px`;
    flake.style.height = flake.style.width;
    flake.style.animationDuration = `${6 + Math.random() * 10}s`;
    flake.style.animationDelay = `${Math.random() * 6}s`;
    flake.style.opacity = 0.3 + Math.random() * 0.4;
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
  
  // Regular stars - reduced count for subtlety
  const starCount = 50;
  for (let i = 0; i < starCount; i++) {
    const star = document.createElement('div');
    star.className = 'weather-particle star';
    // Make some stars brighter
    if (Math.random() > 0.9) {
      star.classList.add('bright');
    }
    star.style.left = `${Math.random() * 100}%`;
    star.style.top = `${Math.random() * 60}%`;
    star.style.animationDuration = `${3 + Math.random() * 4}s`;
    star.style.animationDelay = `${Math.random() * 5}s`;
    container.appendChild(star);
  }
  
  // Single subtle shooting star
  const shootingStar = document.createElement('div');
  shootingStar.className = 'weather-particle shooting-star';
  shootingStar.style.left = `${20 + Math.random() * 40}%`;
  shootingStar.style.top = `${5 + Math.random() * 15}%`;
  shootingStar.style.animationDelay = `${5 + Math.random() * 5}s`;
  shootingStar.style.animationDuration = `${3 + Math.random() * 2}s`;
  container.appendChild(shootingStar);
}

function createWindEffect(container) {
  const streakCount = 8;
  
  for (let i = 0; i < streakCount; i++) {
    const streak = document.createElement('div');
    streak.className = 'weather-particle wind-streak';
    streak.style.top = `${10 + Math.random() * 80}%`;
    streak.style.width = `${50 + Math.random() * 100}px`;
    streak.style.animationDuration = `${2 + Math.random() * 2}s`;
    streak.style.animationDelay = `${Math.random() * 4}s`;
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

if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    const assetVersion = document.documentElement?.dataset?.assetVersion;
    const swUrl = assetVersion ? `/sw.js?v=${encodeURIComponent(assetVersion)}` : '/sw.js';
    navigator.serviceWorker.register(swUrl).catch((error) => {
      console.warn('Service worker registration failed', error);
    });
  });
}
