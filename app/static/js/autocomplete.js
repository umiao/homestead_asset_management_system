/**
 * LFU Cache-based Autocomplete Component
 *
 * Provides popup menu suggestions for form inputs based on usage frequency.
 * Features:
 * - Real-time filtering as user types
 * - Keyboard navigation (arrow keys, enter, escape)
 * - Mouse click selection
 * - LFU-based ranking
 */

class AutocompleteInput {
    constructor(inputElement, options = {}) {
        this.input = inputElement;
        this.fieldType = options.fieldType || 'category';
        this.minChars = options.minChars || 0;
        this.maxSuggestions = options.maxSuggestions || 10;
        this.debounceMs = options.debounceMs || 200;
        this.household_id = options.household_id || 1;

        this.dropdown = null;
        this.suggestions = [];
        this.selectedIndex = -1;
        this.debounceTimer = null;

        this.init();
    }

    init() {
        // Create dropdown container
        this.dropdown = document.createElement('div');
        this.dropdown.className = 'autocomplete-dropdown';
        this.dropdown.style.display = 'none';

        // Position dropdown relative to input
        this.input.parentElement.style.position = 'relative';
        this.input.parentElement.appendChild(this.dropdown);

        // Bind event listeners
        this.input.addEventListener('input', this.onInput.bind(this));
        this.input.addEventListener('focus', this.onFocus.bind(this));
        this.input.addEventListener('blur', this.onBlur.bind(this));
        this.input.addEventListener('keydown', this.onKeyDown.bind(this));

        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!this.input.contains(e.target) && !this.dropdown.contains(e.target)) {
                this.hideDropdown();
            }
        });
    }

    async onInput(e) {
        const query = this.input.value.trim();

        // Clear previous debounce timer
        if (this.debounceTimer) {
            clearTimeout(this.debounceTimer);
        }

        // Debounce API call
        this.debounceTimer = setTimeout(async () => {
            if (query.length >= this.minChars) {
                await this.fetchSuggestions(query);
            } else {
                // Show top suggestions if no query
                await this.fetchSuggestions('');
            }
        }, this.debounceMs);
    }

    async onFocus(e) {
        // Show suggestions on focus
        const query = this.input.value.trim();
        await this.fetchSuggestions(query);
    }

    onBlur(e) {
        // Delay hiding to allow click on dropdown items
        setTimeout(() => {
            this.hideDropdown();
        }, 200);
    }

    onKeyDown(e) {
        if (!this.dropdown || this.dropdown.style.display === 'none') {
            return;
        }

        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                this.selectNext();
                break;
            case 'ArrowUp':
                e.preventDefault();
                this.selectPrevious();
                break;
            case 'Enter':
                e.preventDefault();
                if (this.selectedIndex >= 0) {
                    this.selectSuggestion(this.suggestions[this.selectedIndex]);
                }
                break;
            case 'Escape':
                e.preventDefault();
                this.hideDropdown();
                break;
        }
    }

    async fetchSuggestions(query) {
        try {
            const url = `/api/autocomplete/suggestions/${this.fieldType}?query=${encodeURIComponent(query)}&limit=${this.maxSuggestions}&household_id=${this.household_id}`;
            const response = await fetch(url);

            if (!response.ok) {
                console.error('Failed to fetch suggestions:', response.statusText);
                this.suggestions = [];
                this.hideDropdown();
                return;
            }

            this.suggestions = await response.json();
            this.renderDropdown();
        } catch (error) {
            console.error('Error fetching autocomplete suggestions:', error);
            this.suggestions = [];
            this.hideDropdown();
        }
    }

    renderDropdown() {
        // Clear dropdown
        this.dropdown.innerHTML = '';

        if (this.suggestions.length === 0) {
            this.hideDropdown();
            return;
        }

        // Reset selection
        this.selectedIndex = -1;

        // Create suggestion items
        this.suggestions.forEach((suggestion, index) => {
            const item = document.createElement('div');
            item.className = 'autocomplete-item';

            // Main value
            const valueSpan = document.createElement('span');
            valueSpan.className = 'autocomplete-value';
            valueSpan.textContent = suggestion.value;
            item.appendChild(valueSpan);

            // Frequency badge
            if (suggestion.frequency > 1) {
                const badge = document.createElement('span');
                badge.className = 'autocomplete-badge';
                badge.textContent = suggestion.frequency;
                badge.title = `Used ${suggestion.frequency} times`;
                item.appendChild(badge);
            }

            // Click handler
            item.addEventListener('click', () => {
                this.selectSuggestion(suggestion);
            });

            // Hover handler
            item.addEventListener('mouseenter', () => {
                this.setSelectedIndex(index);
            });

            this.dropdown.appendChild(item);
        });

        this.showDropdown();
    }

    selectNext() {
        if (this.suggestions.length === 0) return;

        this.selectedIndex = (this.selectedIndex + 1) % this.suggestions.length;
        this.updateSelection();
    }

    selectPrevious() {
        if (this.suggestions.length === 0) return;

        if (this.selectedIndex <= 0) {
            this.selectedIndex = this.suggestions.length - 1;
        } else {
            this.selectedIndex--;
        }
        this.updateSelection();
    }

    setSelectedIndex(index) {
        this.selectedIndex = index;
        this.updateSelection();
    }

    updateSelection() {
        const items = this.dropdown.querySelectorAll('.autocomplete-item');
        items.forEach((item, index) => {
            if (index === this.selectedIndex) {
                item.classList.add('selected');
                item.scrollIntoView({ block: 'nearest' });
            } else {
                item.classList.remove('selected');
            }
        });
    }

    selectSuggestion(suggestion) {
        this.input.value = suggestion.value;
        this.hideDropdown();

        // Trigger input event for any listeners
        this.input.dispatchEvent(new Event('input', { bubbles: true }));
        this.input.dispatchEvent(new Event('change', { bubbles: true }));
    }

    showDropdown() {
        this.dropdown.style.display = 'block';
    }

    hideDropdown() {
        this.dropdown.style.display = 'none';
        this.selectedIndex = -1;
    }

    destroy() {
        if (this.dropdown && this.dropdown.parentElement) {
            this.dropdown.parentElement.removeChild(this.dropdown);
        }
        this.input = null;
        this.dropdown = null;
        this.suggestions = [];
    }
}

// Global autocomplete instances registry
window.autocompleteInstances = window.autocompleteInstances || {};

/**
 * Initialize autocomplete for an input element
 *
 * @param {string} inputId - ID of the input element
 * @param {string} fieldType - Type of field (category, location_path, unit)
 * @param {object} options - Additional options
 */
function initAutocomplete(inputId, fieldType, options = {}) {
    const inputElement = document.getElementById(inputId);

    if (!inputElement) {
        console.error(`Autocomplete: Input element '${inputId}' not found`);
        return null;
    }

    // Destroy existing instance if present
    if (window.autocompleteInstances[inputId]) {
        window.autocompleteInstances[inputId].destroy();
    }

    // Create new instance
    const autocomplete = new AutocompleteInput(inputElement, {
        fieldType,
        ...options
    });

    // Store instance
    window.autocompleteInstances[inputId] = autocomplete;

    return autocomplete;
}

/**
 * Initialize autocomplete cache from existing data (one-time setup)
 */
async function initializeAutocompleteCache() {
    try {
        const response = await fetch('/api/autocomplete/initialize', {
            method: 'POST'
        });

        if (response.ok) {
            const result = await response.json();
            console.log('Autocomplete cache initialized:', result);
            return result;
        } else {
            console.error('Failed to initialize autocomplete cache:', response.statusText);
        }
    } catch (error) {
        console.error('Error initializing autocomplete cache:', error);
    }
}

/**
 * Get autocomplete statistics
 */
async function getAutocompleteStats(fieldType = null) {
    try {
        const url = fieldType
            ? `/api/autocomplete/statistics?field_type=${fieldType}`
            : '/api/autocomplete/statistics';

        const response = await fetch(url);

        if (response.ok) {
            return await response.json();
        } else {
            console.error('Failed to get autocomplete stats:', response.statusText);
        }
    } catch (error) {
        console.error('Error getting autocomplete stats:', error);
    }
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        AutocompleteInput,
        initAutocomplete,
        initializeAutocompleteCache,
        getAutocompleteStats
    };
}
