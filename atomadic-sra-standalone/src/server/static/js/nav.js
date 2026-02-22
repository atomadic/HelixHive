/**
 * SRA // Unified Navigation & Device Substrate
 * v4.2.0.0 - Neuro-Aesthetic Edition
 */

const NavSubstrate = {
    isMobile: localStorage.getItem('sra_device_mode') === 'mobile',

    init() {
        this.applyDeviceMode();
        this.injectDeviceToggle();
        console.log("[Nav] Substrate Manifested. Device:", this.isMobile ? 'Mobile' : 'PC');
    },

    toggleDeviceMode() {
        this.isMobile = !this.isMobile;
        localStorage.setItem('sra_device_mode', this.isMobile ? 'mobile' : 'pc');
        this.applyDeviceMode();
        showToast(`Switched to ${this.isMobile ? 'Mobile' : 'PC'} Mode`, 'info');
    },

    applyDeviceMode() {
        const toggle = document.getElementById('device-toggle');
        const isMobile = document.body.classList.toggle('mobile-mode', this.isMobile); // Use toggle with force parameter
        const navItems = [
            { id: 'dashboard', label: 'GENESIS', icon: '💎' },
            { id: 'modules', label: 'AUTOPOIESIS', icon: '🏗️' },
            { id: 'research', label: 'RESEARCH', icon: '🔍' },
            { id: 'agents', label: 'AGENTS', icon: '👤' },
            { id: 'goals', label: 'GOALS', icon: '🎯' },
            { id: 'evolution', label: 'EVOLUTION', icon: '🧬' },
            { id: 'ecosystem', label: 'ECOSYSTEM', icon: '🌐' },
            { id: 'marketplace', label: 'MARKET', icon: '🛒' },
            { id: 'knowledge', label: 'KNOWLEDGE', icon: '📖' },
            { id: 'logs', label: 'LOGS', icon: '📋' },
            { id: 'settings', label: 'SYSTEM', icon: '⚙️' }
        ];
        if (toggle) { // Check if toggle button exists before updating its text
            toggle.innerHTML = this.isMobile ? '<i>📱</i> MOBILE' : '<i>💻</i> PC';
        }

        // Persist to Sovereign Vault
        if (window.Persistence) {
            window.Persistence.set('device_mode', this.isMobile ? 'mobile' : 'pc');
        }
    },

    injectDeviceToggle() {
        const header = document.querySelector('.system-status');
        if (!header) return;

        const toggleBtn = document.createElement('button');
        toggleBtn.id = 'device-toggle'; // Add ID for easier access
        toggleBtn.className = 'btn btn-device-toggle';
        toggleBtn.innerHTML = this.isMobile ? '<i>📱</i> MOBILE' : '<i>💻</i> PC';
        toggleBtn.onclick = () => {
            this.toggleDeviceMode();
            toggleBtn.innerHTML = this.isMobile ? '<i>📱</i> MOBILE' : '<i>💻</i> PC';
        };

        // Insert before the initialize button
        const initBtn = document.querySelector('.btn-evolution');
        header.insertBefore(toggleBtn, initBtn);
    }
};

window.addEventListener('DOMContentLoaded', () => NavSubstrate.init());
