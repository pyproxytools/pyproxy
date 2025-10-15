let countdown = 2;

async function fetchAllData() {
    try {
        const [monitoringRes, configRes, blockedRes] = await Promise.all([
            fetch('/api/status'),
            fetch('/api/settings'),
            fetch('/api/filtering')
        ]);

        const monitoring = await monitoringRes.json();
        const config = await configRes.json();
        const blocked = await blockedRes.json();

        document.getElementById('status-section').innerHTML = `
            <h2>${I18N["Main Process"]}</h2>
            <p><strong>${I18N["Name:"]}</strong> ${monitoring.name}</p>
            <p><strong>${I18N["PID:"]}</strong> ${monitoring.pid}</p>
            <p><strong>${I18N["Status:"]}</strong> <span class="badge ${monitoring.status}">${monitoring.status}</span></p>
            <p><strong>${I18N["Start Time:"]}</strong> ${monitoring.start_time}</p>
        `;

        document.getElementById('subprocesses-section').innerHTML = `
            <h2>${I18N["Subprocesses"]}</h2>
            ${Object.values(monitoring.subprocesses).map(proc => `
                <div class="subprocess">
                    <h3>${proc.name}</h3>
                    <p><strong>${I18N["PID:"]}</strong> ${proc.pid}</p>
                    <p><strong>${I18N["Status:"]}</strong> <span class="badge ${proc.status}">${proc.status}</span></p>
                    <ul>${proc.threads.map(t => `<li>${t.name} (${t.thread_id})</li>`).join('')}</ul>
                </div>
            `).join('')}
        `;

        document.getElementById('connections-table-container').innerHTML = `
            ${monitoring.active_connections.length === 0
                ? `<p>${I18N["No active connections."]}</p>`
                : `
                <table class="generic-table">
                    <thead>
                        <tr>
                            <th>${I18N["Client"]}</th>
                            <th>${I18N["Target"]}</th>
                            <th>${I18N["Sent"]}</th>
                            <th>${I18N["Received"]}</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${monitoring.active_connections.map(conn => `
                            <tr>
                                <td>${conn.client_ip}:${conn.client_port}</td>
                                <td>${conn.target_domain} (${conn.target_ip}:${conn.target_port})</td>
                                <td>${conn.bytes_sent} ${I18N["bytes"]}</td>
                                <td>${formatBytes(conn.bytes_received)}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
                `}
        `;

        document.getElementById('config-section').innerHTML = `
            <h2>${I18N["Configuration"]} ${config.debug ? '<span class="badge stopped small">DEBUG</span>' : ''}</h2>
            <p><strong>${I18N["Port:"]}</strong> ${config.port ? `<span class="path">${config.port}</span>` : '<span class="checkmark false">✗</span>'}</p>
            <p><strong>${I18N["Flask Port:"]}</strong> ${config.flask_port ? `<span class="path">${config.flask_port}</span>` : '<span class="checkmark false">✗</span>'}</p>
            <p><strong>${I18N["HTML 403:"]}</strong> ${config.html_403 ? `<span class="path">${config.html_403}</span>` : '<span class="checkmark false">✗</span>'}</p>
            <h3>${I18N["Filter Configuration"]} <span class="checkmark ${config.filter_config.no_filter ? 'false' : ''}">${config.filter_config.no_filter ? '✗' : '✓'}</span></h3>
            <p><strong>${I18N["Blocked Sites File:"]}</strong> ${config.filter_config.blocked_sites ? `<span class="path">${config.filter_config.blocked_sites}</span>` : '<span class="checkmark false">✗</span>'}</p>
            <p><strong>${I18N["Blocked URL File:"]}</strong> ${config.filter_config.blocked_url ? `<span class="path">${config.filter_config.blocked_url}</span>` : '<span class="checkmark false">✗</span>'}</p>
            <p><strong>${I18N["Filter Mode:"]}</strong> <span class="path">${config.filter_config.filter_mode}</span></p>
            <h3>${I18N["Logger Configuration"]}</h3>
            <p><strong>${I18N["Access Log:"]}</strong> ${config.logger_config.no_logging_access ? '<span class="checkmark false">✗</span>' : '<span class="checkmark">✓</span>'} ${config.logger_config.access_log ? `<span class="path">${config.logger_config.access_log}</span>` : '<span class="checkmark false">✗</span>'}</p>
            <p><strong>${I18N["Block Log:"]}</strong> ${config.logger_config.no_logging_block ? '<span class="checkmark false">✗</span>' : '<span class="checkmark">✓</span>'} ${config.logger_config.block_log ? `<span class="path">${config.logger_config.block_log}</span>` : '<span class="checkmark false">✗</span>'}</p>
            <h3>${I18N["SSL Inspection"]} <span class="checkmark ${config.ssl_config.ssl_inspect ? '' : 'false'}">${config.ssl_config.ssl_inspect ? '✓' : '✗'}</span></h3>
            <p><strong>${I18N["Inspect CA Cert:"]}</strong> ${config.ssl_config.inspect_ca_cert ? `<span class="path">${config.ssl_config.inspect_ca_cert}</span>` : '<span class="checkmark false">✗</span>'}</p>
            <p><strong>${I18N["Inspect CA Key:"]}</strong> ${config.ssl_config.inspect_ca_key ? `<span class="path">${config.ssl_config.inspect_ca_key}</span>` : '<span class="checkmark false">✗</span>'}</p>
            <p><strong>${I18N["Inspect certs folder:"]}</strong> ${config.ssl_config.inspect_certs_folder ? `<span class="path">${config.ssl_config.inspect_certs_folder}</span>` : '<span class="checkmark false">✗</span>'}</p>
            <p><strong>${I18N["Cancel inspect:"]}</strong> ${config.ssl_config.cancel_inspect ? `<span class="path">${config.ssl_config.cancel_inspect}</span>` : '<span class="checkmark false">✗</span>'}</p>
        `;

        const searchInput = document.getElementById('connection-search');
        if (searchInput) {
            filterConnections(searchInput.value);
        }

        const blockedSites = blocked.blocked_sites || [];
        const blockedUrls = blocked.blocked_url || [];

        const blockedSection = document.getElementById('blocked-section-container');
        if (blockedSection) {
            blockedSection.innerHTML = `
            <div class="blocked-subsection">
                <h3>${I18N["Blocked sites"]}</h3>
                ${blockedSites.length === 0
                ? '<p>${I18N["No blocked sites."]}</p>'
                : `
                <table class="generic-table filtering-table">
                    <thead>
                    <tr>
                        <th>${I18N["Domain"]}</th>
                        <th>${I18N["Action"]}</th>
                    </tr>
                    </thead>
                    <tbody>
                    ${blockedSites.map(site => `
                        <tr>
                        <td>${site}</td>
                        <td>
                            <button onclick="handleUnblock('domain', '${site}')">${I18N["Unblock"]}</button>
                        </td>
                        </tr>
                    `).join('')}
                    </tbody>
                </table>
                `}
            </div>
            <div class="blocked-subsection">
                <h3>${I18N["Blocked URLs"]}</h3>
                ${blockedUrls.length === 0
                ? '<p>${I18N["No URLs blocked."]}</p>'
                : `
                <table class="generic-table filtering-table">
                    <thead>
                    <tr>
                        <th>${I18N["URL"]}</th>
                        <th>${I18N["Action"]}</th>
                    </tr>
                    </thead>
                    <tbody>
                    ${blockedUrls.map(url => `
                        <tr>
                        <td>${url}</td>
                        <td>
                            <button onclick="handleUnblock('url', '${url}')">${I18N["Unblock"]}</button>
                        </td>
                        </tr>
                    `).join('')}
                    </tbody>
                </table>
                `}
            </div>
            `;
        }

        const blockedSearchInput = document.getElementById('blocked-search');
        if (blockedSearchInput) {
            filterBlocked(blockedSearchInput.value);
        }

    } catch (err) {
        console.error('${I18N["Error loading data:"]}', err);
    }
    countdown = 2;
}

function formatBytes(bytes) {
    if (bytes === 0) return '0 B';
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return (bytes / Math.pow(1024, i)).toFixed(2) + ' ' + sizes[i];
}

function handleUnblock(type, value) {
  fetch('/api/filtering', {
    method: 'DELETE',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      type: type,
      value: value
    }),
  })
  .then(response => {
    if (!response.ok) {
      alert(`${I18N["Error while deleting :"]} ${value}`);
    } else {
      fetchAllData();
    }
  })
  .catch(err => {
    console.error('${I18N["Fetching error:"]}', err);
    alert('${I18N["Network error:"]}');
  });
}

function updateCountdown() {
    document.getElementById('refresh-timer').textContent = formatCountdown(countdown);
}

function formatCountdown(seconds) {
    const m = String(Math.floor(seconds / 60)).padStart(2, '0');
    const s = String(seconds % 60).padStart(2, '0');
    return `${m}:${s}`;
}

function filterConnections(filter) {
    filter = filter.toLowerCase();
    const rows = document.querySelectorAll('#connections-table-container tbody tr');
    rows.forEach(row => {
        const client = row.children[0].textContent.toLowerCase();
        const target = row.children[1].textContent.toLowerCase();

        row.querySelectorAll('td').forEach(td => {
            td.innerHTML = td.textContent;
        });

        const match = client.includes(filter) || target.includes(filter);
        row.style.display = match ? '' : 'none';

        if (match && filter.length > 0) {
            if (client.includes(filter)) {
                const originalText = row.children[0].textContent;
                const regex = new RegExp(`(${filter})`, 'gi');
                row.children[0].innerHTML = originalText.replace(regex, '<span class="highlight">$1</span>');
            }
            if (target.includes(filter)) {
                const originalText = row.children[1].textContent;
                const regex = new RegExp(`(${filter})`, 'gi');
                row.children[1].innerHTML = originalText.replace(regex, '<span class="highlight">$1</span>');
            }
        }
    });
}

function filterBlocked(filter) {
    filter = filter.toLowerCase();

    document.querySelectorAll('.blocked-subsection table').forEach(table => {
        table.querySelectorAll('tbody tr').forEach(row => {
            const text = row.children[0].textContent.toLowerCase();
            const match = text.includes(filter);
            row.style.display = match ? '' : 'none';

            row.children[0].innerHTML = row.children[0].textContent;

            if (match && filter.length > 0) {
                const originalText = row.children[0].textContent;
                const regex = new RegExp(`(${filter})`, 'gi');
                row.children[0].innerHTML = originalText.replace(regex, '<span class="highlight">$1</span>');
            }
        });
    });
}

setInterval(() => {
    countdown--;
    if (countdown <= 0) fetchAllData();
    updateCountdown();
}, 1000);

const tabs = document.querySelectorAll('.tab');
const contents = document.querySelectorAll('.tab-content');

function activateTab(tab) {
    tabs.forEach(t => {
        t.classList.remove('active');
        t.setAttribute('aria-selected', 'false');
        t.setAttribute('tabindex', '-1');
    });
    contents.forEach(c => c.classList.remove('active'));

    tab.classList.add('active');
    tab.setAttribute('aria-selected', 'true');
    tab.setAttribute('tabindex', '0');
    const contentId = tab.getAttribute('aria-controls');
    document.getElementById(contentId).classList.add('active');

    localStorage.setItem('activeTabId', tab.id);
}

tabs.forEach(tab => {
    tab.addEventListener('click', () => {
        activateTab(tab);
    });

    tab.addEventListener('keydown', e => {
        let index = Array.from(tabs).indexOf(e.target);
        if (e.key === 'ArrowRight') {
            index = (index + 1) % tabs.length;
            tabs[index].focus();
        } else if (e.key === 'ArrowLeft') {
            index = (index - 1 + tabs.length) % tabs.length;
            tabs[index].focus();
        }
    });
});

window.addEventListener('DOMContentLoaded', () => {
    const savedTabId = localStorage.getItem('activeTabId');
    if (savedTabId) {
        const savedTab = document.getElementById(savedTabId);
        if (savedTab) {
            activateTab(savedTab);
        } else {
            activateTab(tabs[0]);
        }
    } else {
        activateTab(tabs[0]);
    }

    const searchInput = document.getElementById('connection-search');
    if (searchInput) {
        searchInput.addEventListener('input', () => {
            filterConnections(searchInput.value);
        });
    }

    const blockedSearchInput = document.getElementById('blocked-search');
    if (blockedSearchInput) {
        blockedSearchInput.addEventListener('input', () => {
            filterBlocked(blockedSearchInput.value);
        });
    }

    document.getElementById('add-block-form').addEventListener('submit', function(event) {
        event.preventDefault();

        const type = document.getElementById('block-type').value;
        const value = document.getElementById('block-value').value.trim();

        if (!value) {
            alert('${I18N["Please enter a value to block."]}');
            return;
        }

        fetch('/api/filtering', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                type: type,
                value: value
            }),
        })
        .then(response => {
            if (response.ok) {
                document.getElementById('block-value').value = '';
                fetchAllData();
            } else {
                alert(`${I18N["Error adding :"]} ${value}`);
            }
        })
        .catch(err => {
            console.error('${I18N["Network error:"]}', err);
            alert('${I18N["Network error:"]}');
        });
    });

    fetchAllData();
    updateCountdown();
});

function toggleLangDropdown() {
    const dropdown = document.getElementById("langDropdown");
    dropdown.style.display = dropdown.style.display === "flex" ? "none" : "flex";
}

document.addEventListener("click", (e) => {
    const dropdown = document.getElementById("langDropdown");
    const selector = document.querySelector(".lang-selector");
    if (!selector.contains(e.target)) {
        dropdown.style.display = "none";
    }
});