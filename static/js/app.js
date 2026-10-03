// ================= FINTRACK PRO APPLICATION LOGIC =================

// State variables
let currentYear;
let currentMonth;
let todayStr = '';
let selectedDate = '';
let selectedAccountId = null; // null means all accounts
let accountsList = [];
let categoriesList = [];
let monthSummaries = {};
let dayTransactions = [];
let currentDayFilter = 'all';
let currentTxType = 'debit';
let currentCurrency = '₹';

// Month names
const MONTH_NAMES = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December'
];

const WEEKDAY_NAMES = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

// ------------------- INITIALIZATION -------------------
document.addEventListener('DOMContentLoaded', async () => {
  updateCurrencySymbols();

  // Setup preset logo radio highlights
  document.querySelectorAll('input[name="preset_logo"]').forEach(radio => {
    radio.addEventListener('change', (e) => {
      document.querySelectorAll('.preset-logo-option').forEach(el => {
        el.classList.remove('border-indigo-500', 'text-indigo-400');
        el.classList.add('border-slate-700', 'text-slate-300');
      });
      const parentLabel = e.target.closest('label');
      if (parentLabel) {
        parentLabel.classList.remove('border-slate-700', 'text-slate-300');
        parentLabel.classList.add('border-indigo-500', 'text-indigo-400');
      }
    });
  });

  // Fetch initial data
  await fetchCategories();
  await fetchAccounts();

  // Initialize with server today or client today (minimum starting at October 2026)
  const today = new Date();
  currentYear = today.getFullYear();
  currentMonth = today.getMonth() + 1; // 1-12
  
  if (currentYear < 2026 || (currentYear === 2026 && currentMonth < 10)) {
    currentYear = 2026;
    currentMonth = 10;
  }

  todayStr = formatDateISO(today);
  selectedDate = (todayStr < '2026-10-01') ? '2026-10-01' : todayStr;

  await loadCalendarMonth(currentYear, currentMonth);
  await loadDateDetails(selectedDate);
  await fetchOverviewStats();

  if (window.lucide) {
    lucide.createIcons();
  }
});

function updateCurrencySymbols() {
  const symbolEl = document.getElementById('tx-currency-symbol');
  if (symbolEl) symbolEl.textContent = '₹';
}

function formatCurrency(amount) {
  const num = Number(amount) || 0;
  return `₹${num.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function formatDateISO(d) {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

// ------------------- TOAST NOTIFICATIONS -------------------
function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  
  let bgClass = 'bg-slate-800 border-slate-700 text-slate-100';
  let iconName = 'info';
  
  if (type === 'success') {
    bgClass = 'bg-emerald-950/90 border-emerald-600/50 text-emerald-200';
    iconName = 'check-circle';
  } else if (type === 'error') {
    bgClass = 'bg-rose-950/90 border-rose-600/50 text-rose-200';
    iconName = 'alert-triangle';
  } else if (type === 'warning') {
    bgClass = 'bg-amber-950/90 border-amber-600/50 text-amber-200';
    iconName = 'shield-alert';
  }

  toast.className = `toast flex items-center gap-2.5 px-4 py-3 rounded-2xl border shadow-xl text-xs font-semibold backdrop-blur-md ${bgClass}`;
  toast.innerHTML = `
    <i data-lucide="${iconName}" class="w-4 h-4 shrink-0"></i>
    <span>${message}</span>
  `;

  container.appendChild(toast);
  if (window.lucide) lucide.createIcons();

  setTimeout(() => {
    toast.style.transition = 'all 0.3s ease';
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// ------------------- RENDER LOGO HELPER -------------------
function renderLogoHTML(logo, name = 'Account', customClass = 'w-7 h-7') {
  if (!logo || logo === 'preset_bank') {
    return `<div class="${customClass} rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 flex items-center justify-center p-1.5"><i data-lucide="landmark" class="w-full h-full"></i></div>`;
  }
  if (logo === 'preset_wallet') {
    return `<div class="${customClass} rounded-xl bg-purple-500/10 text-purple-400 border border-purple-500/20 flex items-center justify-center p-1.5"><i data-lucide="wallet" class="w-full h-full"></i></div>`;
  }
  if (logo === 'preset_card') {
    return `<div class="${customClass} rounded-xl bg-blue-500/10 text-blue-400 border border-blue-500/20 flex items-center justify-center p-1.5"><i data-lucide="credit-card" class="w-full h-full"></i></div>`;
  }
  if (logo === 'preset_cash') {
    return `<div class="${customClass} rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center justify-center p-1.5"><i data-lucide="banknote" class="w-full h-full"></i></div>`;
  }
  // Custom uploaded image file
  return `<div class="${customClass} rounded-xl overflow-hidden bg-slate-800 border border-slate-700 shrink-0">
    <img src="${logo}" alt="${name}" class="account-logo-img" onerror="this.src='/static/icons/preset_bank.svg'">
  </div>`;
}

// ------------------- ACCOUNTS SECTION -------------------
async function fetchAccounts() {
  try {
    const res = await fetch('/api/accounts');
    accountsList = await res.json();
    renderAccountsShelf();
    populateAccountSelects();
  } catch (err) {
    console.error('Error fetching accounts:', err);
    showToast('Failed to load accounts', 'error');
  }
}

function renderAccountsShelf() {
  const shelf = document.getElementById('accounts-shelf');
  const countBadge = document.getElementById('accounts-count-badge');
  if (countBadge) countBadge.textContent = accountsList.length;

  if (accountsList.length === 0) {
    shelf.innerHTML = `
      <div class="col-span-full py-8 text-center bg-slate-850/40 rounded-2xl border border-dashed border-slate-800">
        <i data-lucide="landmark" class="w-8 h-8 text-slate-500 mx-auto mb-2"></i>
        <p class="text-xs text-slate-400 font-medium">No accounts added yet.</p>
        <button onclick="openAddAccountModal()" class="mt-2.5 px-3 py-1.5 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-500 text-white transition">
          + Add Your First Bank / Wallet
        </button>
      </div>
    `;
    if (window.lucide) lucide.createIcons();
    return;
  }

  let html = '';
  accountsList.forEach(acc => {
    const isActive = selectedAccountId === acc.id;
    const isNegative = acc.current_balance < 0;

    html += `
      <div onclick="filterByAccount(${acc.id})" class="account-card rounded-2xl p-4 flex flex-col justify-between ${isActive ? 'active-filter' : ''}">
        <!-- Top Row: Logo, Name & Type -->
        <div class="flex items-start justify-between gap-3">
          <div class="flex items-center gap-2.5">
            ${renderLogoHTML(acc.logo, acc.name, 'w-9 h-9')}
            <div class="overflow-hidden">
              <h4 class="font-bold text-sm text-slate-100 truncate" title="${acc.name}">${acc.name}</h4>
              <span class="text-[10px] uppercase font-bold tracking-wider text-slate-400 block">${acc.account_type}</span>
            </div>
          </div>
          
          <div class="flex items-center gap-1">
            <button onclick="event.stopPropagation(); openEditAccountModal(${acc.id})" title="Edit account details and logo" class="text-slate-400 hover:text-indigo-400 p-1 rounded-lg hover:bg-slate-800 transition">
              <i data-lucide="pencil" class="w-3.5 h-3.5"></i>
            </button>
            <button onclick="event.stopPropagation(); deleteAccount(${acc.id}, '${acc.name}')" title="Delete account" class="text-slate-400 hover:text-rose-400 p-1 rounded-lg hover:bg-slate-800 transition">
              <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
            </button>
          </div>
        </div>

        <!-- Middle: Dynamic Current Balance -->
        <div class="mt-3">
          <span class="text-[10px] uppercase tracking-wider text-slate-400 font-semibold block">Current Balance</span>
          <div class="font-mono text-base font-extrabold ${isNegative ? 'text-rose-400' : 'text-emerald-400'}">
            ${formatCurrency(acc.current_balance)}
          </div>
        </div>

        <!-- Bottom: Credits & Debits quick stats -->
        <div class="mt-2 pt-2 border-t border-slate-800/80 flex items-center justify-between text-[10px] text-slate-400 font-mono">
          <span class="text-emerald-400">+${formatCurrency(acc.total_credits)}</span>
          <span class="text-rose-400">-${formatCurrency(acc.total_debits)}</span>
        </div>
      </div>
    `;
  });

  shelf.innerHTML = html;
  if (window.lucide) lucide.createIcons();
}

function filterByAccount(accountId) {
  selectedAccountId = (selectedAccountId === accountId) ? null : accountId;
  
  const filterBtn = document.getElementById('filter-all-accounts-btn');
  if (filterBtn) {
    if (selectedAccountId === null) {
      filterBtn.classList.remove('bg-slate-800', 'text-slate-400');
      filterBtn.classList.add('bg-indigo-500/20', 'text-indigo-300');
    } else {
      filterBtn.classList.remove('bg-indigo-500/20', 'text-indigo-300');
      filterBtn.classList.add('bg-slate-800', 'text-slate-400');
    }
  }

  renderAccountsShelf();
  loadDateDetails(selectedDate);
}

function populateAccountSelects() {
  const select = document.getElementById('tx-account-select');
  if (!select) return;

  if (accountsList.length === 0) {
    select.innerHTML = '<option value="">No accounts available. Please add an account first.</option>';
    return;
  }

  let options = '';
  accountsList.forEach(acc => {
    options += `<option value="${acc.id}">${acc.name} (${acc.account_type.toUpperCase()} &bull; Balance: ${formatCurrency(acc.current_balance)})</option>`;
  });
  select.innerHTML = options;
}

async function deleteAccount(id, name) {
  if (!confirm(`Are you sure you want to delete "${name}"? All associated transactions will also be permanently deleted.`)) {
    return;
  }

  try {
    const res = await fetch(`/api/accounts/${id}`, { method: 'DELETE' });
    const data = await res.json();
    if (res.ok) {
      showToast(`Account "${name}" deleted`, 'success');
      if (selectedAccountId === id) selectedAccountId = null;
      await fetchAccounts();
      await loadCalendarMonth(currentYear, currentMonth);
      await loadDateDetails(selectedDate);
      await fetchOverviewStats();
    } else {
      showToast(data.error || 'Failed to delete account', 'error');
    }
  } catch (err) {
    showToast('Network error while deleting account', 'error');
  }
}

// ------------------- CALENDAR GENERATION WITH FUTURE LOCKING -------------------
const START_YEAR = 2026;
const START_MONTH = 10; // October 2026

async function loadCalendarMonth(year, month) {
  try {
    // RULE 1: Never allow months before October 2026
    if (year < START_YEAR || (year === START_YEAR && month < START_MONTH)) {
      year = START_YEAR;
      month = START_MONTH;
    }

    const res = await fetch(`/api/calendar/month?year=${year}&month=${month}`);
    const data = await res.json();
    
    todayStr = data.today;
    monthSummaries = data.summaries || {};

    const [todayY, todayM] = todayStr.split('-').map(Number);
    const maxYear = todayY;
    const maxMonth = todayM;

    // RULE 2: Never allow future months; next month unlocks only when that month arrives
    if (year > maxYear || (year === maxYear && month > maxMonth)) {
      year = maxYear;
      month = maxMonth;
    }

    currentYear = year;
    currentMonth = month;

    // Update Month Title & Stats
    const titleEl = document.getElementById('calendar-month-title');
    if (titleEl) titleEl.textContent = `${MONTH_NAMES[month - 1]} ${year}`;

    const monthCreditEl = document.getElementById('cal-month-credit');
    const monthDebitEl = document.getElementById('cal-month-debit');
    const monthNetEl = document.getElementById('cal-month-net');

    if (monthCreditEl) monthCreditEl.textContent = `+${formatCurrency(data.month_total_credit)}`;
    if (monthDebitEl) monthDebitEl.textContent = `-${formatCurrency(data.month_total_debit)}`;
    if (monthNetEl) {
      const net = data.month_net;
      monthNetEl.textContent = `${net >= 0 ? '+' : '-'}${formatCurrency(Math.abs(net))}`;
      monthNetEl.className = `text-sm sm:text-base font-bold font-mono ${net >= 0 ? 'text-emerald-400' : 'text-rose-400'}`;
    }

    // Update Navigation Button States (Prev & Next buttons)
    const prevBtn = document.getElementById('cal-prev-btn');
    const nextBtn = document.getElementById('cal-next-btn');

    const isMinMonth = (year === START_YEAR && month === START_MONTH);
    const isMaxMonth = (year === maxYear && month >= maxMonth);

    if (prevBtn) {
      prevBtn.disabled = isMinMonth;
      prevBtn.title = isMinMonth ? "Calendar starts from October 2026. No previous months available." : "Previous Month";
    }

    if (nextBtn) {
      nextBtn.disabled = isMaxMonth;
      nextBtn.title = isMaxMonth ? "Future months are locked. Next month unlocks on that month." : "Next Month";
    }

    renderCalendarGrid(year, month);
  } catch (err) {
    console.error('Error loading calendar month:', err);
    showToast('Failed to load calendar data', 'error');
  }
}

function renderCalendarGrid(year, month) {
  const grid = document.getElementById('calendar-days-grid');
  if (!grid) return;

  grid.innerHTML = '';

  const firstDayOfMonth = new Date(year, month - 1, 1);
  const daysInMonth = new Date(year, month, 0).getDate();

  // Day of week for 1st day (0 = Sunday, 1 = Monday, ..., 6 = Saturday)
  // We want Monday as index 0, ..., Sunday as index 6
  let startingWeekday = firstDayOfMonth.getDay() - 1;
  if (startingWeekday < 0) startingWeekday = 6;

  // RULE: DO NOT show previous months dates - render invisible alignment spacer cells
  for (let i = startingWeekday - 1; i >= 0; i--) {
    const cell = document.createElement('div');
    cell.className = 'calendar-day-cell invisible opacity-0 pointer-events-none';
    grid.appendChild(cell);
  }

  // Current month days (e.g. Oct 1 to Oct 31)
  for (let d = 1; d <= daysInMonth; d++) {
    const dateStr = `${year}-${String(month).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
    
    // Future dates are LOCKED (visible but cannot add any info)
    const isFuture = dateStr > todayStr;
    const isToday = dateStr === todayStr;
    const isSelected = dateStr === selectedDate;

    const summary = monthSummaries[dateStr] || { credit: 0, debit: 0, count: 0 };

    const cell = document.createElement('div');
    cell.className = `calendar-day-cell ${isFuture ? 'locked' : 'unlocked'} ${isToday ? 'is-today' : ''} ${isSelected ? 'selected' : ''}`;
    cell.dataset.date = dateStr;

    // Header inside cell: Date number + Lock icon (if future)
    let headerHTML = `
      <div class="flex items-center justify-between">
        <span class="day-number-badge w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold text-slate-200">
          ${d}
        </span>
        ${isFuture ? `<span title="Future date locked" class="text-amber-400/80"><i data-lucide="lock" class="w-3.5 h-3.5"></i></span>` : ''}
        ${isToday ? `<span class="w-2 h-2 rounded-full bg-indigo-400 animate-ping"></span>` : ''}
      </div>
    `;

    // Activity indicator inside cell (Credits & Debits)
    let indicatorsHTML = `<div class="mt-1 space-y-0.5">`;
    if (!isFuture && summary.count > 0) {
      if (summary.credit > 0) {
        indicatorsHTML += `
          <div class="flex items-center gap-1 text-[10px] font-mono font-bold text-emerald-400 truncate">
            <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 shrink-0"></span>
            <span class="truncate">+${formatCurrency(summary.credit)}</span>
          </div>
        `;
      }
      if (summary.debit > 0) {
        indicatorsHTML += `
          <div class="flex items-center gap-1 text-[10px] font-mono font-bold text-rose-400 truncate">
            <span class="w-1.5 h-1.5 rounded-full bg-rose-500 shrink-0"></span>
            <span class="truncate">-${formatCurrency(summary.debit)}</span>
          </div>
        `;
      }
    } else if (isFuture) {
      indicatorsHTML += `
        <div class="text-[9px] font-medium text-slate-500 italic flex items-center gap-1">
          <span>Locked</span>
        </div>
      `;
    }
    indicatorsHTML += `</div>`;

    cell.innerHTML = headerHTML + indicatorsHTML;

    // Click handler
    cell.addEventListener('click', () => {
      onDateCellClicked(dateStr, isFuture);
    });

    grid.appendChild(cell);
  }

  // RULE: DO NOT show future months dates - render invisible alignment spacer cells
  const totalCells = startingWeekday + daysInMonth;
  const remainingCells = (7 - (totalCells % 7)) % 7;
  for (let i = 1; i <= remainingCells; i++) {
    const cell = document.createElement('div');
    cell.className = 'calendar-day-cell invisible opacity-0 pointer-events-none';
    grid.appendChild(cell);
  }

  if (window.lucide) lucide.createIcons();
}

function onDateCellClicked(dateStr, isFuture) {
  selectedDate = dateStr;

  // Update selected class in grid
  document.querySelectorAll('.calendar-day-cell').forEach(c => {
    if (c.dataset.date === dateStr) {
      c.classList.add('selected');
    } else {
      c.classList.remove('selected');
    }
  });

  loadDateDetails(dateStr);

  if (isFuture) {
    // Open locked date modal alert
    openLockedModal(dateStr);
  }
}

function prevMonth() {
  if (currentYear === START_YEAR && currentMonth === START_MONTH) {
    showToast('The tracking calendar starts from October 2026. No previous months available.', 'warning');
    return;
  }
  currentMonth--;
  if (currentMonth < 1) {
    currentMonth = 12;
    currentYear--;
  }
  loadCalendarMonth(currentYear, currentMonth);
}

function nextMonth() {
  const [todayY, todayM] = todayStr.split('-').map(Number);
  if (currentYear > todayY || (currentYear === todayY && currentMonth >= todayM)) {
    showToast('Future months are locked! Next month unlocks automatically when that date and month arrives.', 'warning');
    return;
  }
  currentMonth++;
  if (currentMonth > 12) {
    currentMonth = 1;
    currentYear++;
  }
  loadCalendarMonth(currentYear, currentMonth);
}

function jumpToToday() {
  const [todayY, todayM] = todayStr.split('-').map(Number);
  currentYear = todayY;
  currentMonth = todayM;
  selectedDate = todayStr;
  loadCalendarMonth(currentYear, currentMonth);
  loadDateDetails(selectedDate);
}

// ------------------- DATE DETAILS PANEL & TRANSACTIONS -------------------
async function loadDateDetails(dateStr) {
  if (!dateStr) return;

  try {
    let url = `/api/transactions/date/${dateStr}`;
    if (selectedAccountId) url += `?account_id=${selectedAccountId}`;

    const res = await fetch(url);
    const data = await res.json();

    dayTransactions = data.transactions || [];

    // Parse date for title
    const [y, m, d] = dateStr.split('-').map(Number);
    const dateObj = new Date(y, m - 1, d);
    const weekday = WEEKDAY_NAMES[dateObj.getDay()];
    const monthName = MONTH_NAMES[m - 1];

    // Update panel header
    const displayEl = document.getElementById('selected-date-display');
    const subEl = document.getElementById('selected-date-sub');
    const badgeEl = document.getElementById('selected-day-badge');
    const lockBadgeEl = document.getElementById('lock-state-badge');
    const addBtn = document.getElementById('add-tx-btn-for-date');

    if (displayEl) displayEl.textContent = `${monthName} ${d}, ${y}`;
    if (subEl) subEl.textContent = weekday;

    const isToday = dateStr === todayStr;
    const isFuture = dateStr > todayStr;

    if (badgeEl) {
      if (isToday) {
        badgeEl.textContent = 'Today';
        badgeEl.className = 'px-2 py-0.5 text-[11px] font-bold rounded-md bg-indigo-500/10 text-indigo-400 border border-indigo-500/20';
      } else if (isFuture) {
        badgeEl.textContent = 'Future Date';
        badgeEl.className = 'px-2 py-0.5 text-[11px] font-bold rounded-md bg-amber-500/10 text-amber-400 border border-amber-500/20';
      } else {
        badgeEl.textContent = 'Past Date';
        badgeEl.className = 'px-2 py-0.5 text-[11px] font-bold rounded-md bg-slate-700 text-slate-300 border border-slate-600';
      }
    }

    if (lockBadgeEl) {
      if (isFuture) {
        lockBadgeEl.innerHTML = `<i data-lucide="lock" class="w-3 h-3"></i> Locked`;
        lockBadgeEl.className = 'px-2 py-0.5 text-[11px] font-bold rounded-md bg-rose-500/10 text-rose-400 border border-rose-500/20 flex items-center gap-1';
      } else {
        lockBadgeEl.innerHTML = `<i data-lucide="unlock" class="w-3 h-3"></i> Unlocked`;
        lockBadgeEl.className = 'px-2 py-0.5 text-[11px] font-bold rounded-md bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1';
      }
    }

    // Disable or enable Add Action button
    if (addBtn) {
      if (isFuture) {
        addBtn.disabled = true;
        addBtn.title = "Future dates are locked from adding records";
      } else {
        addBtn.disabled = false;
        addBtn.title = "Add Credit or Debit for this date";
      }
    }

    // Update Totals
    const creditEl = document.getElementById('day-total-credit');
    const debitEl = document.getElementById('day-total-debit');
    const netEl = document.getElementById('day-net-balance');

    if (creditEl) creditEl.textContent = `+${formatCurrency(data.total_credit)}`;
    if (debitEl) debitEl.textContent = `-${formatCurrency(data.total_debit)}`;
    
    if (netEl) {
      const net = data.net;
      netEl.textContent = `${net >= 0 ? '+' : '-'}${formatCurrency(Math.abs(net))}`;
      netEl.className = `font-mono font-bold ${net >= 0 ? 'text-emerald-400' : 'text-rose-400'}`;
    }

    // Update tab counts
    const countAll = document.getElementById('count-day-all');
    const countCredit = document.getElementById('count-day-credit');
    const countDebit = document.getElementById('count-day-debit');

    if (countAll) countAll.textContent = dayTransactions.length;
    if (countCredit) countCredit.textContent = data.credits.length;
    if (countDebit) countDebit.textContent = data.debits.length;

    renderDayTransactions();
  } catch (err) {
    console.error('Error loading date details:', err);
  }
}

function filterDayTransactions(tab) {
  currentDayFilter = tab;
  
  const tabs = ['all', 'credit', 'debit'];
  tabs.forEach(t => {
    const btn = document.getElementById(`tab-day-${t}`);
    if (btn) {
      if (t === tab) {
        btn.className = 'flex-1 py-1.5 font-bold rounded-lg bg-indigo-600 text-white transition text-center shadow-md';
      } else {
        btn.className = 'flex-1 py-1.5 font-semibold rounded-lg text-slate-400 hover:text-white transition text-center';
      }
    }
  });

  renderDayTransactions();
}

function renderDayTransactions() {
  const list = document.getElementById('day-transactions-list');
  if (!list) return;

  const filtered = dayTransactions.filter(t => {
    if (currentDayFilter === 'all') return true;
    return t.type === currentDayFilter;
  });

  if (filtered.length === 0) {
    list.innerHTML = `
      <div class="text-center py-10 bg-slate-800/30 rounded-2xl border border-dashed border-slate-800 text-slate-500 text-xs">
        <i data-lucide="receipt" class="w-8 h-8 mx-auto mb-2 opacity-30"></i>
        <span>No ${currentDayFilter === 'all' ? '' : currentDayFilter} actions recorded on this date.</span>
      </div>
    `;
    if (window.lucide) lucide.createIcons();
    return;
  }

  let html = '';
  filtered.forEach(tx => {
    const isCredit = tx.type === 'credit';
    const amountColor = isCredit ? 'text-emerald-400' : 'text-rose-400';
    const sign = isCredit ? '+' : '-';
    const categoryIcon = tx.category_icon || '🏷️';
    const categoryName = tx.category_name || (isCredit ? 'Income' : 'Expense');

    html += `
      <div class="p-3 rounded-2xl bg-slate-800/70 border border-slate-700/70 hover:border-slate-600 transition flex items-center justify-between gap-3 group">
        <!-- Left: Category Icon & Details -->
        <div class="flex items-center gap-3 overflow-hidden">
          <div class="w-10 h-10 rounded-xl flex items-center justify-center text-lg shrink-0 shadow-sm" style="background-color: ${tx.category_color || '#4f46e5'}20; border: 1px solid ${tx.category_color || '#4f46e5'}40">
            ${categoryIcon}
          </div>
          <div class="overflow-hidden">
            <div class="flex items-center gap-2">
              <span class="font-bold text-xs text-white truncate">${categoryName}</span>
              <span class="text-[10px] px-1.5 py-0.5 rounded font-mono font-medium ${isCredit ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'}">
                ${tx.type.toUpperCase()}
              </span>
            </div>
            
            <p class="text-[11px] text-slate-400 truncate mt-0.5">${tx.description || 'No description'}</p>
            
            <div class="flex items-center gap-2 mt-1">
              <!-- Account badge with logo -->
              <span class="inline-flex items-center gap-1 text-[10px] font-semibold text-slate-300 bg-slate-900/60 px-2 py-0.5 rounded-md border border-slate-700/60">
                ${renderLogoHTML(tx.account_logo, tx.account_name, 'w-3.5 h-3.5')}
                <span class="truncate max-w-[90px]">${tx.account_name}</span>
              </span>
              ${tx.time ? `<span class="text-[10px] font-mono text-slate-500">${tx.time}</span>` : ''}
            </div>
          </div>
        </div>

        <!-- Right: Amount & Action Buttons (Edit + Delete) -->
        <div class="flex items-center gap-1.5 shrink-0">
          <div class="text-right">
            <span class="font-mono font-extrabold text-sm ${amountColor}">
              ${sign}${formatCurrency(tx.amount)}
            </span>
          </div>
          <button onclick="openEditTransactionModal(${tx.id})" title="Edit transaction action" class="opacity-50 group-hover:opacity-100 text-slate-400 hover:text-indigo-400 p-1.5 rounded-lg hover:bg-slate-750 transition">
            <i data-lucide="pencil" class="w-3.5 h-3.5"></i>
          </button>
          <button onclick="deleteTransaction(${tx.id})" title="Delete entry" class="opacity-50 group-hover:opacity-100 text-slate-400 hover:text-rose-400 p-1.5 rounded-lg hover:bg-slate-750 transition">
            <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
          </button>
        </div>
      </div>
    `;
  });

  list.innerHTML = html;
  if (window.lucide) lucide.createIcons();
}

async function deleteTransaction(txId) {
  if (!confirm('Are you sure you want to delete this transaction?')) return;

  try {
    const res = await fetch(`/api/transactions/${txId}`, { method: 'DELETE' });
    const data = await res.json();
    if (res.ok) {
      showToast('Transaction removed', 'success');
      await fetchAccounts();
      await loadCalendarMonth(currentYear, currentMonth);
      await loadDateDetails(selectedDate);
      await fetchOverviewStats();
    } else {
      showToast(data.error || 'Failed to delete transaction', 'error');
    }
  } catch (err) {
    showToast('Network error while deleting transaction', 'error');
  }
}

// ------------------- ADD / EDIT TRANSACTION MODAL & SUBMIT -------------------
function openAddTransactionModal() {
  if (selectedDate > todayStr) {
    openLockedModal(selectedDate);
    return;
  }

  if (!accountsList || accountsList.length === 0) {
    showToast('Please add a bank or wallet account first!', 'info');
    openAddAccountModal();
    return;
  }

  const modal = document.getElementById('tx-modal');
  const editIdInput = document.getElementById('edit-tx-id');
  const titleEl = document.getElementById('tx-modal-title');
  const dateInput = document.getElementById('tx-date-input');
  const dateDisplay = document.getElementById('tx-modal-date-display');
  const amountInput = document.getElementById('tx-amount-input');
  const descInput = document.getElementById('tx-description-input');

  if (editIdInput) editIdInput.value = '';
  if (titleEl) titleEl.textContent = 'Record Transaction';
  if (dateInput) dateInput.value = selectedDate;
  if (dateDisplay) dateDisplay.textContent = `Date: ${selectedDate} (Unlocked)`;
  if (amountInput) amountInput.value = '';
  if (descInput) descInput.value = '';

  // Select account if currently filtered
  const accountSelect = document.getElementById('tx-account-select');
  if (accountSelect && selectedAccountId) {
    accountSelect.value = selectedAccountId;
  }

  toggleTxType('debit');
  modal.classList.remove('hidden');
  if (window.lucide) lucide.createIcons();
}

function openEditTransactionModal(txId) {
  const tx = dayTransactions.find(t => t.id === txId);
  if (!tx) return;

  const modal = document.getElementById('tx-modal');
  const editIdInput = document.getElementById('edit-tx-id');
  const titleEl = document.getElementById('tx-modal-title');
  const dateInput = document.getElementById('tx-date-input');
  const dateDisplay = document.getElementById('tx-modal-date-display');
  const amountInput = document.getElementById('tx-amount-input');
  const descInput = document.getElementById('tx-description-input');
  const accountSelect = document.getElementById('tx-account-select');
  const submitBtn = document.getElementById('tx-submit-btn');

  if (editIdInput) editIdInput.value = tx.id;
  if (titleEl) titleEl.textContent = `Edit ${tx.type.toUpperCase()} Action`;
  if (dateInput) dateInput.value = tx.date;
  if (dateDisplay) dateDisplay.textContent = `Date: ${tx.date} (Unlocked)`;
  if (amountInput) amountInput.value = tx.amount;
  if (descInput) descInput.value = tx.description || '';

  // Select account
  if (accountSelect) accountSelect.value = tx.account_id;

  // Toggle type and select category
  const debitRadio = document.getElementById('tx-type-debit');
  const creditRadio = document.getElementById('tx-type-credit');
  if (tx.type === 'credit') {
    if (creditRadio) creditRadio.checked = true;
    toggleTxType('credit');
  } else {
    if (debitRadio) debitRadio.checked = true;
    toggleTxType('debit');
  }

  // Pre-select category after populateCategorySelect
  const categorySelect = document.getElementById('tx-category-select');
  if (categorySelect && tx.category_id) {
    categorySelect.value = tx.category_id;
  }

  if (submitBtn) {
    submitBtn.textContent = 'Update Action';
  }

  modal.classList.remove('hidden');
  if (window.lucide) lucide.createIcons();
}

function closeAddTransactionModal() {
  document.getElementById('tx-modal').classList.add('hidden');
}

function toggleTxType(type) {
  currentTxType = type;
  const submitBtn = document.getElementById('tx-submit-btn');
  const iconBadge = document.getElementById('tx-modal-icon-badge');
  const isEditing = Boolean(document.getElementById('edit-tx-id').value);

  if (type === 'credit') {
    submitBtn.textContent = isEditing ? 'Update Credit Action' : 'Save Credit Action (Income)';
    submitBtn.className = 'px-5 py-2.5 rounded-xl text-xs font-bold bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg transition';
    iconBadge.className = 'p-2 rounded-xl bg-emerald-500/10 text-emerald-400';
  } else {
    submitBtn.textContent = isEditing ? 'Update Debit Action' : 'Save Debit Action (Expense)';
    submitBtn.className = 'px-5 py-2.5 rounded-xl text-xs font-bold bg-rose-600 hover:bg-rose-500 text-white shadow-lg transition';
    iconBadge.className = 'p-2 rounded-xl bg-rose-500/10 text-rose-400';
  }

  populateCategorySelect(type);
}

function populateCategorySelect(type) {
  const select = document.getElementById('tx-category-select');
  if (!select) return;

  const filtered = categoriesList.filter(c => c.type === type || c.type === 'both');
  
  if (filtered.length === 0) {
    select.innerHTML = '<option value="">No categories for this type</option>';
    return;
  }

  let html = '';
  filtered.forEach(c => {
    html += `<option value="${c.id}">${c.icon} ${c.name}</option>`;
  });
  select.innerHTML = html;
}

async function handleTransactionSubmit(e) {
  e.preventDefault();
  const form = e.target;
  const formData = new FormData(form);
  const editId = document.getElementById('edit-tx-id').value;
  const accountId = parseInt(formData.get('account_id'));
  if (!accountId || isNaN(accountId)) {
    showToast('Please select or create an account first', 'warning');
    return;
  }

  const payload = {
    account_id: accountId,
    category_id: formData.get('category_id') ? parseInt(formData.get('category_id')) : null,
    type: formData.get('type'),
    amount: parseFloat(formData.get('amount')),
    date: formData.get('date'),
    description: formData.get('description')
  };

  try {
    let url = '/api/transactions';
    let method = 'POST';

    if (editId) {
      url = `/api/transactions/${editId}`;
      method = 'PUT';
    }

    const res = await fetch(url, {
      method: method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();

    if (res.ok) {
      showToast(data.message || (editId ? 'Transaction updated!' : 'Transaction recorded!'), 'success');
      closeAddTransactionModal();
      form.reset();
      
      // Update app state
      await fetchAccounts();
      await loadCalendarMonth(currentYear, currentMonth);
      await loadDateDetails(selectedDate);
      await fetchOverviewStats();
    } else {
      showToast(data.error || 'Failed to save transaction', 'error');
    }
  } catch (err) {
    showToast('Network error while saving transaction', 'error');
  }
}

// ------------------- ACCOUNTS MODAL & SUBMIT -------------------
function openAddAccountModal() {
  const form = document.getElementById('add-account-form');
  if (form) form.reset();

  document.getElementById('edit-account-id').value = '';
  document.getElementById('account-modal-title').textContent = 'Add Bank or Wallet';
  document.getElementById('account-modal-sub').textContent = 'Track balance, logos, and actions for this account';
  document.getElementById('account-submit-btn').textContent = 'Save Account';
  document.getElementById('custom-logo-preview').innerHTML = `<i data-lucide="image" class="w-5 h-5"></i>`;

  // Select preset_bank
  const bankRadio = document.querySelector('input[name="preset_logo"][value="preset_bank"]');
  if (bankRadio) bankRadio.checked = true;
  document.querySelectorAll('.preset-logo-option').forEach(el => {
    el.classList.remove('border-indigo-500', 'text-indigo-400');
    el.classList.add('border-slate-700', 'text-slate-300');
  });
  if (bankRadio && bankRadio.closest('label')) {
    bankRadio.closest('label').classList.add('border-indigo-500', 'text-indigo-400');
  }

  document.getElementById('account-modal').classList.remove('hidden');
  if (window.lucide) lucide.createIcons();
}

function openEditAccountModal(accountId) {
  const acc = accountsList.find(a => a.id === accountId);
  if (!acc) return;

  const form = document.getElementById('add-account-form');
  if (form) form.reset();

  document.getElementById('edit-account-id').value = acc.id;
  document.getElementById('account-modal-title').textContent = `Edit "${acc.name}"`;
  document.getElementById('account-modal-sub').textContent = 'Modify bank/wallet name, logo, type, or balance';
  document.getElementById('account-submit-btn').textContent = 'Save Changes';

  document.getElementById('account-name-input').value = acc.name;
  document.getElementById('account-type-select').value = acc.account_type;
  document.getElementById('account-balance-input').value = acc.initial_balance;
  document.getElementById('account-color-input').value = acc.color || '#4f46e5';

  const preview = document.getElementById('custom-logo-preview');
  document.querySelectorAll('.preset-logo-option').forEach(el => {
    el.classList.remove('border-indigo-500', 'text-indigo-400');
    el.classList.add('border-slate-700', 'text-slate-300');
  });

  if (acc.logo && acc.logo.startsWith('/static/uploads/')) {
    if (preview) {
      preview.innerHTML = `<img src="${acc.logo}" class="w-full h-full object-cover">`;
    }
  } else {
    const radio = document.querySelector(`input[name="preset_logo"][value="${acc.logo}"]`) || document.querySelector('input[name="preset_logo"][value="preset_bank"]');
    if (radio) {
      radio.checked = true;
      if (radio.closest('label')) {
        radio.closest('label').classList.add('border-indigo-500', 'text-indigo-400');
      }
    }
    if (preview) {
      preview.innerHTML = `<i data-lucide="image" class="w-5 h-5"></i>`;
    }
  }

  document.getElementById('account-modal').classList.remove('hidden');
  if (window.lucide) lucide.createIcons();
}

function closeAddAccountModal() {
  document.getElementById('account-modal').classList.add('hidden');
}

function setAccountColor(hex) {
  const colorInput = document.querySelector('input[name="color"]');
  if (colorInput) colorInput.value = hex;
}

function previewLogoFile(e) {
  const file = e.target.files[0];
  const preview = document.getElementById('custom-logo-preview');
  if (file && preview) {
    const reader = new FileReader();
    reader.onload = (event) => {
      preview.innerHTML = `<img src="${event.target.result}" class="w-full h-full object-cover">`;
    };
    reader.readAsDataURL(file);
  }
}

async function handleAccountSubmit(e) {
  e.preventDefault();
  const form = e.target;
  const formData = new FormData(form);
  const editId = document.getElementById('edit-account-id').value;

  try {
    let url = '/api/accounts';
    if (editId) {
      url = `/api/accounts/${editId}`;
    }

    const res = await fetch(url, {
      method: 'POST',
      body: formData
    });
    const data = await res.json();

    if (res.ok) {
      showToast(data.message || (editId ? 'Account updated successfully!' : 'Account added successfully!'), 'success');
      closeAddAccountModal();
      form.reset();
      document.getElementById('custom-logo-preview').innerHTML = `<i data-lucide="image" class="w-5 h-5"></i>`;
      await fetchAccounts();
      await loadCalendarMonth(currentYear, currentMonth);
      await loadDateDetails(selectedDate);
      await fetchOverviewStats();
    } else {
      showToast(data.error || 'Failed to save account', 'error');
    }
  } catch (err) {
    showToast('Network error while saving account', 'error');
  }
}

// ------------------- CATEGORIES MANAGEMENT -------------------
async function fetchCategories() {
  try {
    const res = await fetch('/api/categories');
    categoriesList = await res.json();
    renderCategoriesInModal();
  } catch (err) {
    console.error('Error fetching categories:', err);
  }
}

function openCategoryModal() {
  document.getElementById('category-modal').classList.remove('hidden');
  renderCategoriesInModal();
  if (window.lucide) lucide.createIcons();
}

function closeCategoryModal() {
  document.getElementById('category-modal').classList.add('hidden');
}

function selectCatEmoji(emoji) {
  const input = document.getElementById('new-cat-icon');
  if (input) input.value = emoji;
}

function renderCategoriesInModal() {
  const debitContainer = document.getElementById('debit-categories-list');
  const creditContainer = document.getElementById('credit-categories-list');

  const debitCats = categoriesList.filter(c => c.type === 'debit' || c.type === 'both');
  const creditCats = categoriesList.filter(c => c.type === 'credit' || c.type === 'both');

  if (debitContainer) {
    debitContainer.innerHTML = debitCats.map(c => `
      <div class="flex items-center justify-between p-2 rounded-xl bg-slate-800 border border-slate-700/80 text-xs">
        <div class="flex items-center gap-2 overflow-hidden">
          <span class="text-base">${c.icon}</span>
          <span class="text-slate-200 truncate font-medium">${c.name}</span>
        </div>
        <button onclick="deleteCategory(${c.id}, '${c.name}')" title="Delete category" class="text-slate-500 hover:text-rose-400 p-1 rounded transition">
          <i data-lucide="x" class="w-3.5 h-3.5"></i>
        </button>
      </div>
    `).join('');
  }

  if (creditContainer) {
    creditContainer.innerHTML = creditCats.map(c => `
      <div class="flex items-center justify-between p-2 rounded-xl bg-slate-800 border border-slate-700/80 text-xs">
        <div class="flex items-center gap-2 overflow-hidden">
          <span class="text-base">${c.icon}</span>
          <span class="text-slate-200 truncate font-medium">${c.name}</span>
        </div>
        <button onclick="deleteCategory(${c.id}, '${c.name}')" title="Delete category" class="text-slate-500 hover:text-rose-400 p-1 rounded transition">
          <i data-lucide="x" class="w-3.5 h-3.5"></i>
        </button>
      </div>
    `).join('');
  }

  if (window.lucide) lucide.createIcons();
}

async function handleCategorySubmit(e) {
  e.preventDefault();
  const nameInput = document.getElementById('new-cat-name');
  const typeSelect = document.getElementById('new-cat-type');
  const iconInput = document.getElementById('new-cat-icon');
  const colorInput = document.getElementById('new-cat-color');

  const payload = {
    name: nameInput.value.trim(),
    type: typeSelect.value,
    icon: iconInput.value.trim() || '🏷️',
    color: colorInput.value
  };

  try {
    const res = await fetch('/api/categories', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();

    if (res.ok) {
      showToast(`Category "${payload.name}" created!`, 'success');
      nameInput.value = '';
      await fetchCategories();
      populateCategorySelect(currentTxType);
    } else {
      showToast(data.error || 'Failed to create category', 'error');
    }
  } catch (err) {
    showToast('Network error while adding category', 'error');
  }
}

async function deleteCategory(id, name) {
  if (!confirm(`Delete category "${name}"?`)) return;

  try {
    const res = await fetch(`/api/categories/${id}`, { method: 'DELETE' });
    const data = await res.json();
    if (res.ok) {
      showToast(`Category removed`, 'success');
      await fetchCategories();
      populateCategorySelect(currentTxType);
    } else {
      showToast(data.error || 'Failed to delete category', 'error');
    }
  } catch (err) {
    showToast('Network error', 'error');
  }
}

// ------------------- FUTURE LOCKED MODAL -------------------
function openLockedModal(dateStr) {
  const modal = document.getElementById('locked-date-modal');
  const msg = document.getElementById('locked-modal-msg');
  if (msg) {
    msg.innerHTML = `You clicked <strong>${dateStr}</strong>, which is in the future. In accordance with expense tracking rules, future dates remain locked until that date arrives. You can view calendar dates, but cannot add transactions ahead of time.`;
  }
  modal.classList.remove('hidden');
  if (window.lucide) lucide.createIcons();
}

function closeLockedModal() {
  document.getElementById('locked-date-modal').classList.add('hidden');
}

// ------------------- OVERVIEW STATS -------------------
async function fetchOverviewStats() {
  try {
    const res = await fetch('/api/stats/overview');
    const data = await res.json();

    const netWorthEl = document.getElementById('nav-net-worth');
    const monthCreditEl = document.getElementById('nav-month-credit');
    const monthDebitEl = document.getElementById('nav-month-debit');

    if (netWorthEl) netWorthEl.textContent = formatCurrency(data.net_worth);
    if (monthCreditEl) monthCreditEl.textContent = `+${formatCurrency(data.month_credits)}`;
    if (monthDebitEl) monthDebitEl.textContent = `-${formatCurrency(data.month_debits)}`;
  } catch (err) {
    console.error('Error fetching overview stats:', err);
  }
}
