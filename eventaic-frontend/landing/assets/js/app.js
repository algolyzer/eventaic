// Mobile nav
const menuBtn = document.getElementById('menuBtn');
const mobileNav = document.getElementById('mobileNav');
window.closeNav = () => mobileNav.classList.remove('open');
menuBtn?.addEventListener('click', () => mobileNav.classList.toggle('open'));

// Theme toggle
const themeToggle = document.getElementById('themeToggle');
if (themeToggle) {
    themeToggle.addEventListener('click', () => {
        const light = document.documentElement.classList.toggle('light');
        if (light) {
            document.documentElement.style.setProperty('--bg', '#f7f7fb');
            document.documentElement.style.setProperty('--bg-soft', '#ffffff');
            document.documentElement.style.setProperty('--text', '#111116');
            document.documentElement.style.setProperty('--muted', '#5b5e6a');
            document.documentElement.style.setProperty('--card', 'rgba(0,0,0,0.05)');
            document.documentElement.style.setProperty('--border', 'rgba(0,0,0,0.08)');
            document.documentElement.style.setProperty('--shadow', '0 10px 25px rgba(16,24,40,0.08)');
        } else {
            document.documentElement.style.removeProperty('--bg');
            document.documentElement.style.removeProperty('--bg-soft');
            document.documentElement.style.removeProperty('--text');
            document.documentElement.style.removeProperty('--muted');
            document.documentElement.style.removeProperty('--card');
            document.documentElement.style.removeProperty('--border');
            document.documentElement.style.removeProperty('--shadow');
        }
    });
}

// Year
const yearEl = document.getElementById('year');
if (yearEl) yearEl.textContent = new Date().getFullYear();

// Reveal on scroll
const io = new IntersectionObserver((entries) => {
    entries.forEach(e => {
        if (e.isIntersecting) {
            e.target.classList.add('in');
            io.unobserve(e.target);
        }
    });
}, {threshold: 0.12});
document.querySelectorAll('.reveal').forEach(el => io.observe(el));

// Counter animation
const counters = document.querySelectorAll('.num');
const co = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const el = entry.target;
            const targetRaw = el.getAttribute('data-count');
            const target = parseFloat((targetRaw || '0').replace('<', ''));
            const isLess = (targetRaw || '').includes('<');
            let cur = 0;
            const dur = 1400;
            const start = performance.now();

            function step(t) {
                const p = Math.min((t - start) / dur, 1);
                cur = target * p;
                el.textContent = (isLess ? '<' : '') + (target > 50 ? Math.round(cur) : (Math.round(cur * 10) / 10).toFixed(1));
                if (p < 1) requestAnimationFrame(step);
            }

            requestAnimationFrame(step);
            co.unobserve(el);
        }
    })
}, {threshold: 0.6});
counters.forEach(c => co.observe(c));

// Parallax
const parallaxEls = document.querySelectorAll('.parallax [data-depth]');
let lastY = window.scrollY;
let ticking = false;

function onScroll() {
    lastY = window.scrollY;
    if (!ticking) {
        requestAnimationFrame(updateParallax);
        ticking = true;
    }
}

function updateParallax() {
    parallaxEls.forEach(el => {
        const depth = parseFloat(el.getAttribute('data-depth')) || 0.1;
        el.style.transform = `translate3d(0, ${lastY * depth * -0.2}px, 0)`;
    });
    ticking = false;
}

const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
if (!reduceMotion) {
    document.addEventListener('scroll', onScroll, {passive: true});
    updateParallax();
}

// Demo simulate + auto-improve magic
const simulateBtn = document.getElementById('simulateBtn');
const iterateBtn = document.getElementById('iterateBtn');
const adTitle = document.getElementById('adTitle');
const adDesc = document.getElementById('adDesc');
const kws = document.getElementById('kws');
const hashes = document.getElementById('hashes');
const scores = document.getElementById('scores');
const screen = document.getElementById('screen');
const adImg = document.getElementById('adImg');
const metaRow = document.getElementById('metaRow');

function chip(txt) {
    const s = document.createElement('span');
    s.className = 'pill';
    s.textContent = txt;
    return s;
}

function rand(min, max) {
    return Math.random() * (max - min) + min;
}

function pick(arr) {
    return arr[Math.floor(Math.random() * arr.length)];
}

function shuffle(arr) {
    return arr.slice().sort(() => Math.random() - .5);
}

function genSVG({title, subtitle, hue = 260}) {
    const bg1 = `hsl(${hue},85%,58%)`;
    const bg2 = `hsl(${(hue + 70) % 360},85%,58%)`;
    const text = `#0b0b11`;
    const svg = `<?xml version='1.0' encoding='UTF-8'?>\n<svg xmlns='http://www.w3.org/2000/svg' width='1200' height='675' viewBox='0 0 1200 675'>\n  <defs>\n    <linearGradient id='g' x1='0' y1='0' x2='1' y2='1'>\n      <stop offset='0%' stop-color='${bg1}'/>\n      <stop offset='100%' stop-color='${bg2}'/>\n    </linearGradient>\n  </defs>\n  <rect width='1200' height='675' rx='32' fill='url(#g)'/>\n  <g font-family='Inter,Arial' fill='${text}'>\n    <text x='60' y='340' font-size='82' font-weight='900'>${title}</text>\n    <text x='60' y='420' font-size='40' opacity='0.85'>${subtitle}</text>\n  </g>\n</svg>`;
    return 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svg);
}

const seed = {
    event: 'Black Friday',
    category: 'Electronics',
    city: 'New York',
    titles: [
        'Doors Open. Prices Down. Go.',
        'Midnight Mega Drop — Go.',
        'Black Friday, Unlocked.',
        'Instant Tech Deals, Live.',
        'Flash Cuts. Big Wins.'
    ],
    descs: [
        'Save big on laptops, wearables, and more — today only.',
        'NYC-only blitz pricing on top tech. Limited stock.',
        'Hot prices, zero waiting. Move now.',
        'Top tech, tiny prices. While stock lasts.',
        'Lightning offers refreshed every hour.'
    ],
    kw: ['discount', 'electronics', 'deal', 'sale', 'laptop', 'wearable', 'doorbuster', 'savebig'],
    tags: ['#BlackFriday', '#TechDeals', '#Sale', '#NowLive', '#Eventaic']
};

let scoreState = {rel: 9.1, clr: 8.7, psu: 8.9, safe: 9.6, ctr: 4.5};
let lastHue = 260;

function renderScores() {
    scores.innerHTML = '';
    ['Relevance ' + scoreState.rel.toFixed(1), 'Clarity ' + scoreState.clr.toFixed(1), 'Persuasion ' + scoreState.psu.toFixed(1), 'Brand Safety ' + scoreState.safe.toFixed(1), 'CTR ' + scoreState.ctr.toFixed(1) + '%']
        .forEach(s => scores.appendChild(chip(s)));
}

function simulate() {
    metaRow.innerHTML = '';
    metaRow.appendChild(chip('Event: ' + seed.event));
    metaRow.appendChild(chip('Category: ' + seed.category));
    metaRow.appendChild(chip('City: ' + seed.city));

    const title = pick(seed.titles);
    const desc = pick(seed.descs);
    adTitle.textContent = title;
    adDesc.textContent = desc;

    kws.innerHTML = '';
    shuffle(seed.kw).slice(0, 6).forEach(k => kws.appendChild(chip(k)));
    hashes.innerHTML = '';
    shuffle(seed.tags).slice(0, 5).forEach(h => hashes.appendChild(chip(h)));

    scoreState = {rel: 9.1, clr: 8.7, psu: 8.9, safe: 9.6, ctr: 4.5};
    renderScores();

    lastHue = Math.floor(rand(200, 320));
    adImg.src = genSVG({title: seed.event + ' Tech', subtitle: 'Today only — NYC', hue: lastHue});

    screen.animate([
        {transform: 'scale(.98)', filter: 'brightness(.9)'},
        {transform: 'scale(1)', filter: 'brightness(1)'}
    ], {duration: 350, easing: 'cubic-bezier(.2,.8,.2,1)'});
}

function autoImprove() {
    // Slightly change scores + CTR
    scoreState.rel = Math.min(10, scoreState.rel + rand(0.0, 0.3));
    scoreState.clr = Math.min(10, scoreState.clr + rand(0.0, 0.3));
    scoreState.psu = Math.min(10, scoreState.psu + rand(0.1, 0.5));
    scoreState.safe = Math.min(10, scoreState.safe + rand(0.0, 0.2));
    scoreState.ctr = Math.min(9.9, scoreState.ctr + rand(0.2, 0.9));
    renderScores();

    // Swap title/desc with variants to show "magic"
    const variants = [
        {
            t: 'Black Friday, But Smarter.',
            d: 'Auto-optimized copy for NYC millennials. Stock is moving — grab it fast.'
        },
        {t: 'Deals Just Went Live.', d: 'Phones, laptops, wearables — instant drops while supplies last.'},
        {t: 'Today Only. Tech Goes Low.', d: 'Cart-ready pricing. Free returns. Zero fuss.'},
        {t: '48-Hour Tech Rush.', d: 'Dynamic discounts, refreshed every hour. Don’t miss out.'}
    ];
    const pickV = pick(variants);
    adTitle.textContent = pickV.t;
    adDesc.textContent = pickV.d;

    // Shuffle keywords/hashtags lightly
    if (Math.random() > 0.5) {
        const added = pick(['bargain', 'flashsale', 'limited', 'drops', 'bundle']);
        seed.kw.push(added);
    }
    kws.innerHTML = '';
    shuffle(seed.kw).slice(0, 6).forEach(k => kws.appendChild(chip(k)));
    hashes.innerHTML = '';
    const tagExtra = pick(['#PriceDrop', '#NYC', '#NowOrNever', '#TopTech', '#LimitedTime']);
    hashes.appendChild(chip(tagExtra));
    shuffle(seed.tags).slice(0, 4).forEach(h => hashes.appendChild(chip(h)));

    // New colorway image
    lastHue = (lastHue + Math.floor(rand(20, 90))) % 360;
    adImg.src = genSVG({
        title: 'Live Now',
        subtitle: pick(['NYC Black Friday', 'Hot Tech Deals', 'Today Only', 'Flash Sale']),
        hue: lastHue
    });

    screen.animate([
        {transform: 'translateY(3px)', opacity: .9},
        {transform: 'translateY(0)', opacity: 1}
    ], {duration: 320, easing: 'cubic-bezier(.2,.8,.2,1)'});
}

simulateBtn?.addEventListener('click', simulate);
iterateBtn?.addEventListener('click', autoImprove);

// (Optional UX) Demo form: prevent page reload and show a lightweight confirmation
const contactForm = document.getElementById('contactForm');
contactForm?.addEventListener('submit', (e) => {
    e.preventDefault();
    const data = new FormData(contactForm);
    const name = (data.get('name') || '').toString().trim();
    const email = (data.get('email') || '').toString().trim();

    contactForm.reset();
    const msg = document.createElement('p');
    msg.className = 'section-sub';
    msg.setAttribute('role', 'status');
    msg.textContent = `Thanks${name ? `, ${name}` : ''}! We'll email ${email} shortly.`;
    contactForm.insertAdjacentElement('afterend', msg);
});
