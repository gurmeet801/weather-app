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
  const { hasWeatherData, usedCachedLocation, hasLocationParams } = options;

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
}

// Export for use in templates
window.WeatherApp = {
  init: initWeatherApp,
  showState,
  openModal,
  closeModal,
  requestLocation,
};
