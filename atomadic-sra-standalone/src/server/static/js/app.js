
let currentPage = 'logs';
let systemState = {};
let lastM = 0;

// --- Intelligence Flow Background Canvas ---
const canvas = document.getElementById('intel-canvas');
const ctx = canvas.getContext('2d');
let particles = [];

function initCanvas() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    particles = [];
    for (let i = 0; i < 70; i++) {
        particles.push({
            x: Math.random() * canvas.width,
            y: Math.random() * canvas.height,
            size: Math.random() * 2.5 + 0.5,
            speedX: (Math.random() - 0.5) * 0.4,
            speedY: (Math.random() - 0.5) * 0.4,
            color: Math.random() > 0.6 ? '#00f3ff' : '#bc13fe',
            opacity: Math.random() * 0.5 + 0.1
        });
    }
}

function animateCanvas() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    particles.forEach(p => {
        p.x += p.speedX;
        p.y += p.speedY;

        if (p.x < 0) p.x = canvas.width;
        if (p.x > canvas.width) p.x = 0;
        if (p.y < 0) p.y = canvas.height;
        if (p.y > canvas.height) p.y = 0;

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fillStyle = p.color;
        ctx.globalAlpha = p.opacity;
        ctx.shadowBlur = 12;
        ctx.shadowColor = p.color;
        ctx.fill();
    });
    ctx.globalAlpha = 1;
    requestAnimationFrame(animateCanvas);
}

// --- Dashboard Logic ---
async function fetchSystemState() {
    try {
        // Vault metrics
        const response = await fetch('/api/vault/evolution');
        const evos = await response.json();
        const mValue = evos.length * 420;

        if (mValue !== lastM) {
            animateOdometer('header-dm', lastM, mValue);
            lastM = mValue;
        }

        // HelixHive metrics
        const hiveRes = await fetch('/api/hive/state');
        const hiveState = await hiveRes.json();

        document.getElementById('header-tau').innerText = hiveState.tau.toFixed(4);
        document.getElementById('header-j').innerText = hiveState.J.toFixed(2);

        // Heartbeat Pulse on Header
        const header = document.querySelector('header');
        header.style.boxShadow = `0 4px 30px rgba(0, 243, 255, ${0.15 + (hiveState.tau - 0.8) * 0.2})`;

    } catch (e) {
        console.error("State Fetch Failed", e);
    }
}

function animateOdometer(id, start, end) {
    const el = document.getElementById(id);
    const duration = 1500;
    const startTime = performance.now();

    function update(now) {
        const progress = Math.min(1, (now - startTime) / duration);
        const current = Math.floor(start + (end - start) * progress);
        el.innerText = `+${(current / 1000).toFixed(2)}k`;
        if (progress < 1) requestAnimationFrame(update);
    }
    requestAnimationFrame(update);
}

async function loadPage(pageName) {
    if (currentPage !== pageName) {
        document.getElementById('content-container').style.opacity = '0';
        setTimeout(() => performLoad(pageName), 200);
    } else {
        performLoad(pageName);
    }
}

async function performLoad(pageName) {
    currentPage = pageName;

    // Update Sidebar
    document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
    const activeLink = document.querySelector(`.nav-item[data-page="${pageName}"]`);
    if (activeLink) activeLink.classList.add('active');

    // Update Title
    document.getElementById('page-title-display').innerText = pageName.toUpperCase().replace('_', ' ');

    // Load Content
    try {
        const response = await fetch(`/api/vault/${pageName === 'logs' ? 'evolution' : pageName === 'agents' ? 'evolutions' : pageName}`);
        // This is a placeholder logic for dynamic page mounting if not static

        const pageResponse = await fetch(`/static/pages/${pageName}.html`);
        const html = await pageResponse.text();
        const container = document.getElementById('content-container');
        container.innerHTML = html;
        container.style.opacity = '1';

        // Execute inner scripts
        const scripts = container.getElementsByTagName('script');
        for (let s of scripts) {
            const newScript = document.createElement("script");
            newScript.text = s.text;
            document.body.appendChild(newScript).parentNode.removeChild(newScript);
        }
    } catch (e) {
        console.error("Page Load Failed", e);
    }
}

function showToast(msg, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `card pulse`;
    toast.style.padding = '1rem 2rem';
    toast.style.marginBottom = '1rem';
    toast.style.fontSize = '0.8rem';
    toast.style.borderLeft = `5px solid ${type === 'success' ? 'var(--neon-green)' : type === 'error' ? 'var(--neon-pink)' : 'var(--neon-blue)'}`;
    toast.innerText = msg;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(-20px)';
        setTimeout(() => toast.remove(), 500);
    }, 4000);
}

function toggleEvo() {
    showToast("Axiom Resonance Initialized...", "success");
}

// Initial Load
window.addEventListener('resize', initCanvas);
initCanvas();
animateCanvas();

setInterval(fetchSystemState, 3000);
loadPage('dashboard');
fetchSystemState();

// Initialize Nav Substrate if present (v4.2.0.0)
if (typeof NavSubstrate !== 'undefined') {
    NavSubstrate.init();
}
