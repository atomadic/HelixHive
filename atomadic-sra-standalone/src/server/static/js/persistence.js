/**
 * Sovereign Persistence Substrate v4.2.0.0
 * Axiom: Map ≡ Terrain (Rule 1)
 */

const SovereignPersistence = (() => {
    const DB_NAME = 'SRA_SOVEREIGN_VAULT';
    const DB_VERSION = 1;
    const STORE_NAME = 'ui_state';

    let db = null;

    const init = () => {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(DB_NAME, DB_VERSION);

            request.onupgradeneeded = (event) => {
                const db = event.target.result;
                if (!db.objectStoreNames.contains(STORE_NAME)) {
                    db.createObjectStore(STORE_NAME);
                }
            };

            request.onsuccess = (event) => {
                db = event.target.result;
                console.log("[Persistence] Sovereign Vault Online.");
                resolve(db);
            };

            request.onerror = (event) => {
                console.error("[Persistence] Vault Manifestation Failed.", event.target.error);
                reject(event.target.error);
            };
        });
    };

    const set = (key, value) => {
        if (!db) return;
        const transaction = db.transaction([STORE_NAME], 'readwrite');
        const store = transaction.objectStore(STORE_NAME);
        store.put(value, key);
    };

    const get = (key) => {
        return new Promise((resolve) => {
            if (!db) return resolve(null);
            const transaction = db.transaction([STORE_NAME], 'readonly');
            const store = transaction.objectStore(STORE_NAME);
            const request = store.get(key);
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => resolve(null);
        });
    };

    // Auto-sync UI mode
    const syncDeviceMode = async () => {
        const savedMode = await get('device_mode');
        if (savedMode) {
            document.body.classList.toggle('mobile-mode', savedMode === 'mobile');
            const toggle = document.getElementById('device-toggle');
            if (toggle) toggle.innerText = savedMode === 'mobile' ? 'MOBILE' : 'PC';
        }
    };

    return { init, set, get, syncDeviceMode };
})();

// Self-initiation
document.addEventListener('DOMContentLoaded', async () => {
    await SovereignPersistence.init();
    await SovereignPersistence.syncDeviceMode();
});

window.Persistence = SovereignPersistence;
