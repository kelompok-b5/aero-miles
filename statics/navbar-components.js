const NAV_ITEMS = {
  member: [
    { key: 'dashboard',      label: 'Dashboard',      href: '/member/dashboard/' },
    { key: 'identitas',      label: 'Identitas Saya', href: '/member/identitas/' },
    { key: 'klaim-miles',    label: 'Klaim Miles',    href: '/member/claim/' },
    { key: 'transfer-miles', label: 'Transfer Miles', href: '/member/transfer-miles/' },
    { key: 'redeem-hadiah',  label: 'Redeem Hadiah',  href: '/member/redeem-hadiah/' },
    { key: 'beli-package',   label: 'Beli Package',   href: '/member/beli-package/' },
    { key: 'info-tier',      label: 'Info Tier',      href: '/member/info-tier/' },
  ],
  staff: [
    { key: 'dashboard',          label: 'Dashboard',                href: 'dashboard-staf.html'      },
    { key: 'kelola-member',      label: 'Kelola Member',            href: 'kelola-member.html'       },
    { key: 'kelola-klaim',       label: 'Kelola Klaim',             href: 'claim-staff.html'         },
    { key: 'kelola-hadiah',      label: 'Kelola Hadiah & Penyedia', href: 'kelola-hadiah.html'       },
    { key: 'kelola-mitra',       label: 'Kelola Mitra',             href: 'kelola-mitra.html'        },
    { key: 'laporan-transaksi',  label: 'Laporan Transaksi',        href: 'laporan-transaksi.html'   },
  ],
};

const CSS = `
  :host { display: block; }

  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :host {
    --navy:       #0d2137;
    --navy2:      #163352;
    --teal:       #3dbfbf;
    --teal-light: #5fd6d6;
    --gold:       #f0a500;
    --muted:      #6b8499;
  }

  nav {
    position: sticky;
    top: 0;
    z-index: 999;
    font-family: 'Plus Jakarta Sans', sans-serif;
    box-shadow: 0 4px 24px rgba(13,33,55,0.18);
  }

  /* ── MEMBER ──────────────────────────── */
  nav.member {
    background: var(--navy);
    border-bottom: 1px solid rgba(61,191,191,0.15);
  }
  /* ── STAFF ────────────────────────────── */
  nav.staff {
    background: linear-gradient(90deg, var(--navy), var(--navy2));
    border-bottom: 1px solid rgba(240,165,0,0.2);
  }
  /* ── GUEST ───────────────────────────── */
  nav.guest {
    background: var(--navy);
    border-bottom: 1px solid rgba(61,191,191,0.15);
  }

  .inner {
    max-width: 1280px;
    margin: 0 auto;
    padding: 0 2rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 62px;
  }

  /* brand */
  .brand {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    text-decoration: none;
    flex-shrink: 0;
  }
  .brand-icon {
    width: 34px; height: 34px;
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.1rem; font-weight: 800;
  }
  nav.member .brand-icon, nav.guest .brand-icon { background: var(--teal); color: var(--navy); }
  nav.staff   .brand-icon                        { background: var(--gold); color: white;       }
  .brand-name {
    font-size: 1.05rem; font-weight: 800; color: white; letter-spacing: -0.02em;
  }
  nav.member .brand-accent, nav.guest .brand-accent { color: var(--teal); }
  nav.staff   .brand-accent                          { color: var(--gold); }
  .brand-badge {
    font-size: 0.58rem; font-weight: 700; letter-spacing: 0.07em;
    background: rgba(240,165,0,0.15); border: 1px solid rgba(240,165,0,0.3);
    color: var(--gold); border-radius: 5px; padding: 0.1rem 0.45rem;
    vertical-align: middle; margin-left: 0.3rem;
  }

  /* nav links */
  .links {
    display: flex;
    align-items: center;
    gap: 0.15rem;
    flex: 1;
    justify-content: center;
    overflow: hidden;
  }
  .link {
    color: rgba(255,255,255,0.6);
    font-size: 0.78rem; font-weight: 500;
    padding: 0.5rem 0.75rem;
    border-radius: 8px;
    text-decoration: none;
    transition: all 0.18s;
    white-space: nowrap;
  }
  .link:hover { color: white; background: rgba(255,255,255,0.08); }
  nav.member .link.active { color: var(--teal); background: rgba(61,191,191,0.1); }
  nav.staff   .link.active { color: var(--gold); background: rgba(240,165,0,0.1);  }

  /* right side */
  .right { display: flex; align-items: center; gap: 0.5rem; flex-shrink: 0; }

  /* guest buttons */
  .btn-outline {
    background: none; border: 1.5px solid rgba(61,191,191,0.4);
    color: var(--teal); padding: 0.45rem 1.1rem; border-radius: 8px;
    font-family: inherit; font-size: 0.78rem; font-weight: 600;
    cursor: pointer; transition: all 0.18s; text-decoration: none; white-space: nowrap;
  }
  .btn-outline:hover { border-color: var(--teal); background: rgba(61,191,191,0.08); }
  .btn-solid {
    background: var(--teal); border: none;
    color: var(--navy); padding: 0.45rem 1.1rem; border-radius: 8px;
    font-family: inherit; font-size: 0.78rem; font-weight: 700;
    cursor: pointer; transition: all 0.18s; text-decoration: none; white-space: nowrap;
  }
  .btn-solid:hover { background: var(--teal-light); }

  /* user pill */
  .user-pill {
    display: flex; align-items: center; gap: 0.55rem;
    background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.1);
    border-radius: 10px; padding: 0.35rem 0.75rem 0.35rem 0.45rem;
    cursor: pointer; transition: all 0.18s; position: relative;
  }
  .user-pill:hover { background: rgba(255,255,255,0.1); }
  .avatar {
    width: 26px; height: 26px; border-radius: 7px;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.65rem; font-weight: 800;
  }
  nav.member .avatar, nav.guest .avatar { background: var(--teal); color: var(--navy); }
  nav.staff   .avatar                    { background: var(--gold); color: var(--navy); }
  .uname { font-size: 0.75rem; font-weight: 600; color: rgba(255,255,255,0.85); }
  .urole { font-size: 0.63rem; color: rgba(255,255,255,0.4); }
  .chevron { flex-shrink: 0; transition: transform 0.2s; }
  .user-pill.open .chevron { transform: rotate(180deg); }

  /* dropdown */
  .dropdown {
    position: absolute; right: 0; top: calc(100% + 8px);
    background: white; border-radius: 12px; min-width: 170px;
    box-shadow: 0 16px 40px rgba(13,33,55,0.18);
    border: 1.5px solid #e8f0f5; overflow: hidden;
    display: none; flex-direction: column; z-index: 200;
  }
  .dropdown.open { display: flex; }
  .dd-item {
    padding: 0.7rem 1rem; font-size: 0.8rem; font-weight: 500;
    color: var(--navy); cursor: pointer; transition: background 0.15s;
    display: flex; align-items: center; gap: 0.5rem;
    text-decoration: none; border-bottom: 1px solid #f0f5f8;
  }
  .dd-item:last-child { border-bottom: none; }
  .dd-item:hover { background: #f0f8fb; }
  .dd-item.danger { color: #e05252; }
  .dd-item.danger:hover { background: #fff5f5; }

  /* hamburger */
  .hamburger {
    display: none; background: none; border: none;
    cursor: pointer; padding: 0.5rem; border-radius: 8px;
    color: rgba(255,255,255,0.7);
  }
  .hamburger:hover { background: rgba(255,255,255,0.08); color: white; }

  /* mobile menu */
  .mobile-menu { display: none; }
  .mobile-menu.open { display: block; }
  nav.member .mobile-menu, nav.guest .mobile-menu {
    background: var(--navy2);
    border-top: 1px solid rgba(61,191,191,0.1);
  }
  nav.staff .mobile-menu {
    background: var(--navy2);
    border-top: 1px solid rgba(240,165,0,0.1);
  }
  .mobile-link {
    display: block; padding: 0.75rem 2rem;
    font-size: 0.82rem; font-weight: 500;
    color: rgba(255,255,255,0.65); text-decoration: none;
    border-bottom: 1px solid rgba(255,255,255,0.05);
    transition: all 0.15s;
  }
  .mobile-link:hover { color: white; background: rgba(255,255,255,0.05); }
  nav.member .mobile-link.active { color: var(--teal); }
  nav.staff   .mobile-link.active { color: var(--gold); }
  .mobile-link.logout { color: #e05252; }

  @media (max-width: 900px) {
    .links { display: none; }
    .hamburger { display: flex; }
  }
`;

class AeroNavbar extends HTMLElement {
  static get observedAttributes() {
    return ['role', 'active'];
  }

  connectedCallback() {
    this._render();
    this._bindEvents();
  }

  attributeChangedCallback() {
    if (this.shadowRoot) {
      this._render();
      this._bindEvents();
    }
  }

  get _role()   { return this.getAttribute('role')   || 'guest'; }
  get _active() { return this.getAttribute('active') || ''; }
  get _user()   { return window.AERO_USER || null; }

  _render() {
    if (!this.shadowRoot) this.attachShadow({ mode: 'open' });
    this.shadowRoot.innerHTML = `
      <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet"/>
      <style>${CSS}</style>
      ${this._buildNav()}
    `;
  }

  _buildNav() {
    const role = this._role;
    if (role === 'guest')  return this._navGuest();
    if (role === 'member') return this._navMember();
    if (role === 'staff')   return this._navStaff();
    return '';
  }

  // ──────────────── GUEST ────────────────
  _navGuest() {
    return `
      <nav class="guest">
        <div class="inner">
          ${this._brand('guest')}
          <div class="right">
            <a class="btn-outline" href="login.html">Login</a>
            <a class="btn-solid"   href="register.html">Registrasi</a>
          </div>
        </div>
      </nav>
    `;
  }

  // ──────────────── MEMBER ────────────────
  _navMember() {
    const user = this._user || { nama: 'Ahmad Hidayat', singkatan: 'AH', sub: 'Gold · M0042' };
    const links = NAV_ITEMS.member.map(item => `
      <a class="link${this._active === item.key ? ' active' : ''}" href="${item.href}">
        ${item.label}
      </a>
    `).join('');
    const mobileLinks = NAV_ITEMS.member.map(item => `
      <a class="mobile-link${this._active === item.key ? ' active' : ''}" href="${item.href}">
        ${item.label}
      </a>
    `).join('');

    return `
      <nav class="member">
        <div class="inner">
          ${this._brand('member')}
          <div class="links">${links}</div>
          <div class="right">
            <div class="user-pill" data-toggle="dropdown">
              <div class="avatar">${user.singkatan}</div>
              <div>
                <div class="uname">${user.nama}</div>
                <div class="urole">${user.sub}</div>
              </div>
              ${this._chevron()}
              <div class="dropdown" data-dropdown>
                <a class="dd-item" href="profil.html">
                  ${this._iconUser()} Pengaturan Profil
                </a>
                <a class="dd-item danger" href="login.html" data-logout>
                  ${this._iconLogout()} Logout
                </a>
              </div>
            </div>
            <button class="hamburger" data-toggle="mobile" aria-label="Menu">
              ${this._iconMenu()}
            </button>
          </div>
        </div>
        <div class="mobile-menu" data-mobile>
          ${mobileLinks}
          <a class="mobile-link" href="profil.html">Pengaturan Profil</a>
          <a class="mobile-link logout" href="login.html">Logout</a>
        </div>
      </nav>
    `;
  }

  // ──────────────── STAFF ────────────────
  _navStaff() {
    const user = this._user || { nama: 'Siti Nurhaliza', singkatan: 'SN', sub: 'Staff · siti.nurhaliza@mail.com' };
    const links = NAV_ITEMS.staff.map(item => `
      <a class="link${this._active === item.key ? ' active' : ''}" href="${item.href}">
        ${item.label}
      </a>
    `).join('');
    const mobileLinks = NAV_ITEMS.staff.map(item => `
      <a class="mobile-link${this._active === item.key ? ' active' : ''}" href="${item.href}">
        ${item.label}
      </a>
    `).join('');

    return `
      <nav class="staff">
        <div class="inner">
          ${this._brand('staff')}
          <div class="links">${links}</div>
          <div class="right">
            <div class="user-pill" data-toggle="dropdown">
              <div class="avatar">${user.singkatan}</div>
              <div>
                <div class="uname">${user.nama}</div>
                <div class="urole">${user.sub}</div>
              </div>
              ${this._chevron()}
              <div class="dropdown" data-dropdown>
                <a class="dd-item" href="profile-staff.html">
                  ${this._iconUser()} Pengaturan Profil
                </a>
                <a class="dd-item danger" href="login.html" data-logout>
                  ${this._iconLogout()} Logout
                </a>
              </div>
            </div>
            <button class="hamburger" data-toggle="mobile" aria-label="Menu">
              ${this._iconMenu()}
            </button>
          </div>
        </div>
        <div class="mobile-menu" data-mobile>
          ${mobileLinks}
          <a class="mobile-link" href="profile-staff.html">Pengaturan Profil</a>
          <a class="mobile-link logout" href="login.html">Logout</a>
        </div>
      </nav>
    `;
  }

  // ──────────────── HELPERS ────────────────
  _brand(role) {
    const badge = role === 'staff' ? '<span class="brand-badge">STAFF</span>' : '';
    return `
      <a class="brand" href="${role === 'staff' ? 'dashboard-staff.html' : role === 'member' ? 'dashboard-member.html' : 'index.html'}">
        <div class="brand-icon">✈</div>
        <span class="brand-name">Aero<span class="brand-accent">Miles</span>${badge}</span>
      </a>
    `;
  }
  _chevron() {
    return `<svg class="chevron" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.4)" stroke-width="2.5"><polyline points="6 9 12 15 18 9"/></svg>`;
  }
  _iconMenu() {
    return `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>`;
  }
  _iconUser() {
    return `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="8" r="4"/><path d="M4 20c0-4 3.6-7 8-7s8 3 8 7"/></svg>`;
  }
  _iconLogout() {
    return `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>`;
  }

  // ──────────────── EVENTS ────────────────
  _bindEvents() {
    const root = this.shadowRoot;
    if (!root) return;

    // Dropdown toggle
    const pill = root.querySelector('[data-toggle="dropdown"]');
    if (pill) {
      pill.addEventListener('click', (e) => {
        e.stopPropagation();
        const dd = pill.querySelector('[data-dropdown]');
        const isOpen = dd.classList.toggle('open');
        pill.classList.toggle('open', isOpen);
      });
    }

    // Mobile menu toggle
    const burger = root.querySelector('[data-toggle="mobile"]');
    const mobileMenu = root.querySelector('[data-mobile]');
    if (burger && mobileMenu) {
      burger.addEventListener('click', () => {
        mobileMenu.classList.toggle('open');
      });
    }

    // Close dropdown on outside click
    document.addEventListener('click', () => {
      const dd = root.querySelector('[data-dropdown]');
      const pill2 = root.querySelector('.user-pill');
      if (dd) dd.classList.remove('open');
      if (pill2) pill2.classList.remove('open');
    });
  }
}

customElements.define('aero-navbar', AeroNavbar);