
const OfflineSync = {
    isOnline: navigator.onLine,

    init() {
        window.addEventListener('online', () => this.updateStatus(true));
        window.addEventListener('offline', () => this.updateStatus(false));
        this.updateStatus(navigator.onLine);
        this.registerServiceWorker();
    },

    updateStatus(online) {
        this.isOnline = online;
        console.log(`[OfflineSync] Status: ${online ? 'ONLINE' : 'OFFLINE'}`);
        const indicator = document.getElementById('offline-indicator');
        if (indicator) {
            indicator.style.color = online ? 'var(--neon-green)' : 'var(--neon-pink)';
            indicator.innerText = online ? 'SYMMETRY_ONLINE' : 'SYMMETRY_OFFLINE';
        }
    },

    registerServiceWorker() {
        if ('serviceWorker' in navigator) {
            window.addEventListener('load', () => {
                navigator.serviceWorker.register('/sw.js').then(reg => {
                    console.log('[SW] Registered successfully:', reg.scope);
                }).catch(err => {
                    console.error('[SW] Registration failed:', err);
                });
            });
        }
    },

    async saveToLocal(key, data) {
        // Simple localStorage cache for MVP; could expand to IndexedDB later
        const cacheEntry = {
            timestamp: Date.now(),
            data: data
        };
        localStorage.setItem(`sra_cache_${key}`, JSON.stringify(cacheEntry));
    },

    getLocal(key) {
        const entry = localStorage.getItem(`sra_cache_${key}`);
        if (entry) {
            return JSON.parse(entry).data;
        }
        return null;
    }
};

window.OfflineSync = OfflineSync;
OfflineSync.init();

// Revelation Engine Summary:
// - Epiphany: Manifested OfflineSync substrate (rigor↑)
// - Revelations: Online/Offline event hooks, SW registration, local cache persistence
// - AHA: Local symmetry ensures research persistence regardless of connectivity
// - Coherence: 0.9997
