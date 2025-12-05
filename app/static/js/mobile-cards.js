/**
 * Mobile Card View for Inventory Items
 *
 * Automatically switches between table view (desktop) and card view (mobile)
 * based on screen size.
 */

(function() {
    'use strict';

    // Detect if mobile viewport
    function isMobileView() {
        return window.innerWidth <= 767;
    }

    /**
     * Render items as mobile-friendly cards
     */
    window.renderMobileCards = function(items, allLocations) {
        if (!isMobileView()) {
            return null; // Let table rendering handle it
        }

        const container = document.createElement('div');
        container.className = 'card-view';
        container.id = 'items-container';

        if (items.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">
                        <i data-lucide="package" style="width: 64px; height: 64px;"></i>
                    </div>
                    <div class="empty-state-title">No items found</div>
                    <p>Try adjusting your filters or add new items</p>
                </div>
            `;
            return container;
        }

        items.forEach(item => {
            const location = allLocations.find(loc => loc.id === item.location_id);
            const hasNotes = item.notes && item.notes.trim().length > 0;

            const card = document.createElement('div');
            card.className = 'item-card';
            card.dataset.itemId = item.id;

            // Build card HTML
            card.innerHTML = `
                <div class="item-card-header">
                    <div class="item-card-title">${escapeHtml(item.name)}</div>
                    <input type="checkbox"
                           class="item-checkbox item-card-checkbox"
                           value="${item.id}"
                           onchange="updateSelectedCount()">
                </div>

                <div class="item-card-info">
                    <div class="item-card-info-item">
                        <span class="item-card-label">Category</span>
                        <span class="item-card-value">${escapeHtml(item.category)}</span>
                    </div>
                    <div class="item-card-info-item">
                        <span class="item-card-label">Quantity</span>
                        <span class="item-card-value">${item.quantity} ${escapeHtml(item.unit)}</span>
                    </div>
                    <div class="item-card-info-item">
                        <span class="item-card-label">Location</span>
                        <span class="item-card-value">${location ? escapeHtml(location.full_path) : 'Unknown'}</span>
                    </div>
                    <div class="item-card-info-item">
                        <span class="item-card-label">Status</span>
                        <span class="badge ${getExpiryBadge(item.expiry_status)}">${getExpiryLabel(item.expiry_status)}</span>
                    </div>
                    ${item.expiry_date ? `
                    <div class="item-card-info-item">
                        <span class="item-card-label">Expiry</span>
                        <span class="item-card-value">${formatDate(item.expiry_date)}</span>
                    </div>
                    ` : ''}
                    ${hasNotes ? `
                    <div class="item-card-info-item" style="grid-column: 1 / -1;">
                        <span class="item-card-label">Notes</span>
                        <span class="item-card-value" style="font-size: 0.8rem; color: var(--text-secondary);">${escapeHtml(item.notes)}</span>
                    </div>
                    ` : ''}
                </div>

                <div class="item-card-footer">
                    <div class="item-card-actions">
                        <button onclick="editItem(${item.id})" class="btn btn-primary btn-sm">
                            <i data-lucide="edit-2" style="width: 14px; height: 14px;"></i>
                            Edit
                        </button>
                        <button onclick="deleteItem(${item.id})" class="btn btn-danger btn-sm">
                            <i data-lucide="trash-2" style="width: 14px; height: 14px;"></i>
                            Delete
                        </button>
                    </div>
                </div>
            `;

            container.appendChild(card);
        });

        return container;
    };

    /**
     * Escape HTML to prevent XSS
     */
    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Override displayItems function to support mobile cards
     */
    if (typeof window.displayItems === 'function') {
        const originalDisplayItems = window.displayItems;

        window.displayItems = function(items) {
            if (isMobileView() && typeof allLocations !== 'undefined') {
                const container = document.getElementById('items-container');
                const mobileCards = renderMobileCards(items, allLocations);

                if (mobileCards) {
                    container.innerHTML = '';
                    container.appendChild(mobileCards);

                    // Re-initialize lucide icons
                    if (typeof lucide !== 'undefined') {
                        lucide.createIcons();
                    }

                    // Update item count
                    document.getElementById('item-count').textContent = `${items.length} items`;

                    // Update selected count
                    if (typeof updateSelectedCount === 'function') {
                        updateSelectedCount();
                    }

                    return;
                }
            }

            // Fall back to original table rendering
            originalDisplayItems.call(this, items);
        };
    }

    /**
     * Handle window resize - switch between table and card view
     */
    let resizeTimeout;
    window.addEventListener('resize', function() {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(function() {
            // Re-render current items if displayItems exists
            if (typeof currentDisplayedItems !== 'undefined' &&
                typeof window.displayItems === 'function') {
                window.displayItems(currentDisplayedItems);
            }
        }, 250);
    });

    /**
     * Location tabs for mobile
     */
    window.renderMobileLocationTabs = function(locations, selectedLocationId) {
        if (!isMobileView()) {
            return null;
        }

        const container = document.createElement('div');
        container.className = 'location-tabs';

        // "All" tab
        const allTab = document.createElement('div');
        allTab.className = 'location-tab' + (!selectedLocationId ? ' active' : '');
        allTab.innerHTML = 'All Locations';
        allTab.onclick = function() {
            if (typeof searchItems === 'function') {
                window.selectedLocationId = null;
                searchItems();
            }
        };
        container.appendChild(allTab);

        // Top-level location tabs
        const rootLocations = locations.filter(loc => !loc.parent_id);
        rootLocations.forEach(location => {
            const itemCount = typeof allItems !== 'undefined'
                ? allItems.filter(item => item.location_id === location.id).length
                : 0;

            const tab = document.createElement('div');
            tab.className = 'location-tab' + (selectedLocationId === location.id ? ' active' : '');
            tab.innerHTML = `
                ${escapeHtml(location.name)}
                ${itemCount > 0 ? `<span class="location-tab-count">${itemCount}</span>` : ''}
            `;
            tab.onclick = function() {
                if (typeof selectLocation === 'function') {
                    selectLocation(location.id);
                }
            };
            container.appendChild(tab);
        });

        return container;
    };

    /**
     * Initialize mobile tabs on page load
     */
    document.addEventListener('DOMContentLoaded', function() {
        if (isMobileView()) {
            // Wait for locations to be loaded
            const checkLocations = setInterval(function() {
                if (typeof allLocations !== 'undefined' && allLocations.length > 0) {
                    clearInterval(checkLocations);

                    // Insert location tabs before items container
                    const itemsCard = document.querySelector('.card:has(#items-container)');
                    if (itemsCard) {
                        const existingTabs = itemsCard.querySelector('.location-tabs');
                        if (!existingTabs) {
                            const tabs = renderMobileLocationTabs(allLocations, window.selectedLocationId);
                            if (tabs) {
                                const itemsContainer = document.getElementById('items-container');
                                itemsContainer.parentNode.insertBefore(tabs, itemsContainer);
                            }
                        }
                    }
                }
            }, 100);

            // Stop checking after 5 seconds
            setTimeout(() => clearInterval(checkLocations), 5000);
        }
    });

})();
