(function () {
  function showToast(message) {
    let toast = document.querySelector('.ui-toast');
    if (!toast) {
      toast = document.createElement('div');
      toast.className = 'ui-toast';
      toast.setAttribute('role', 'status');
      toast.setAttribute('aria-live', 'polite');
      document.body.appendChild(toast);
    }

    toast.textContent = message;
    toast.classList.add('is-visible');
    window.clearTimeout(showToast.timer);
    showToast.timer = window.setTimeout(function () {
      toast.classList.remove('is-visible');
    }, 2200);
  }

  function normalize(value) {
    return value.trim().toLowerCase();
  }

  function setActive(button, selector) {
    const group = button.closest(selector);
    if (!group) return;
    group.querySelectorAll('button, label').forEach(function (item) {
      item.classList.remove('is-active');
    });
    button.classList.add('is-active');
  }

  function rowStatus(row) {
    const status =
      row.querySelector('.review-status, .user-presence, .repo-status, .notification-dot');
    if (!status) return '';
    if (status.classList.contains('notification-dot')) return 'unread';
    return normalize(status.textContent);
  }

  function applyTextFilter(input, selector) {
    const scope = input.closest('main') || document;
    const query = normalize(input.value);
    scope.querySelectorAll(selector).forEach(function (item) {
      const text = normalize(item.textContent);
      item.classList.toggle('is-filter-hidden', query.length > 0 && !text.includes(query));
    });
  }

  function applyButtonFilter(button, rowsSelector) {
    const label = normalize(button.textContent).replace(/\(\d+\)/g, '').trim();
    const scope = button.closest('main') || document;
    scope.querySelectorAll(rowsSelector).forEach(function (row) {
      const status = rowStatus(row);
      const shouldShow =
        label === 'all' ||
        status.includes(label) ||
        (label === 'revision' && status.includes('revision')) ||
        (label === 'pending' && status.includes('pending')) ||
        (label === 'compiled' && status.includes('compiled')) ||
        (label === 'active' && status === 'active') ||
        (label === 'inactive' && status === 'inactive') ||
        (label === 'unread' && row.classList.contains('is-unread'));

      row.classList.toggle('is-filter-hidden', !shouldShow);
    });
  }

  function bindSearches() {
    const searchMap = [
      ['.review-search input', '.review-table-card tbody tr'],
      ['.users-search input', '.users-table-card tbody tr'],
      ['.repo-search input', '.repo-document-row'],
      ['.area-search input', '.area-card'],
      ['.conversation-search input', '.conversation-item'],
    ];

    searchMap.forEach(function (entry) {
      document.querySelectorAll(entry[0]).forEach(function (input) {
        input.addEventListener('input', function () {
          applyTextFilter(input, entry[1]);
        });
      });
    });
  }

  function bindFilterTabs() {
    const filterMap = [
      ['.review-filter-tabs', '.review-table-card tbody tr'],
      ['.users-filter-tabs', '.users-table-card tbody tr'],
      ['.notification-filters', '.notification-row'],
    ];

    filterMap.forEach(function (entry) {
      document.querySelectorAll(entry[0] + ' button').forEach(function (button) {
        button.addEventListener('click', function () {
          setActive(button, entry[0]);
          applyButtonFilter(button, entry[1]);
        });
      });
    });
  }

  function bindSelectableGroups() {
    [
      '.department-list',
      '.subarea-list',
      '.score-row',
      '.conversation-list',
      '.review-pagination',
    ].forEach(function (selector) {
      document.querySelectorAll(selector + ' button').forEach(function (button) {
        button.addEventListener('click', function () {
          setActive(button, selector);
        });
      });
    });
  }

  function bindSettingsTabs() {
    document.querySelectorAll('.settings-tab[data-settings-tab]').forEach(function (button) {
      button.addEventListener('click', function () {
        const target = button.dataset.settingsTab;
        const layout = button.closest('.settings-layout');
        if (!layout || !target) return;

        setActive(button, '.settings-tabs');
        layout.querySelectorAll('.settings-tab').forEach(function (tab) {
          tab.setAttribute('aria-selected', tab === button ? 'true' : 'false');
        });
        layout.querySelectorAll('.settings-panel').forEach(function (panel) {
          const isTarget = panel.dataset.settingsPanel === target;
          panel.hidden = !isTarget;
          panel.classList.toggle('is-active', isTarget);
        });
      });
    });
  }

  function bindNotifications() {
    document.querySelectorAll('.notification-dismiss').forEach(function (button) {
      button.addEventListener('click', function () {
        const row = button.closest('.notification-row');
        if (!row) return;
        row.style.opacity = '0';
        row.style.transform = 'translateX(16px)';
        window.setTimeout(function () {
          row.remove();
          showToast('Notification dismissed');
        }, 180);
      });
    });

    document.querySelectorAll('.notification-row').forEach(function (row) {
      row.addEventListener('click', function (event) {
        if (event.target.closest('button')) return;
        row.classList.remove('is-unread');
        const dot = row.querySelector('.notification-dot');
        if (dot) dot.remove();
        showToast('Notification marked as viewed');
      });
    });
  }

  function addChatMessage(input, listSelector, mineClass) {
    const text = input.value.trim();
    if (!text) {
      showToast('Type a message first');
      return;
    }

    const list = document.querySelector(listSelector);
    if (!list) return;

    const article = document.createElement('article');
    article.className = mineClass;
    article.innerHTML =
      '<div class="message-bubble"></div><time>Now</time>';
    article.querySelector('.message-bubble').textContent = text;
    list.appendChild(article);
    input.value = '';
    list.scrollTop = list.scrollHeight;
    showToast('Message sent');
  }

  function bindMessaging() {
    document.querySelectorAll('.message-composer button').forEach(function (button) {
      button.addEventListener('click', function () {
        const input = button.closest('.message-composer').querySelector('input');
        addChatMessage(input, '.message-list', 'message-row is-mine');
      });
    });

    document.querySelectorAll('.message-composer input').forEach(function (input) {
      input.addEventListener('keydown', function (event) {
        if (event.key === 'Enter') {
          event.preventDefault();
          addChatMessage(input, '.message-list', 'message-row is-mine');
        }
      });
    });

    document.querySelectorAll('.suggested-prompts button').forEach(function (button) {
      button.addEventListener('click', function () {
        const input = document.querySelector('.composer-row input');
        if (!input) return;
        input.value = button.textContent.trim();
        input.focus();
      });
    });

    document.querySelectorAll('.composer-row button').forEach(function (button) {
      button.addEventListener('click', function () {
        const input = button.closest('.composer-row').querySelector('input');
        const text = input.value.trim();
        if (!text) {
          showToast('Choose a prompt or type a question');
          return;
        }
        showToast('Question submitted to Smart Companion');
        input.value = '';
      });
    });
  }

  function downloadReport() {
    const body = [
      'JMCFI AMS Report',
      'Academic Year 2025-2026',
      '',
      'Overall Readiness: 74.3%',
      'Total Submissions: 247',
      'Compliance Rate: 73.7%',
      'Overdue Items: 12',
    ].join('\n');
    const blob = new Blob([body], { type: 'text/plain' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = 'jmcfi-ams-report.txt';
    link.click();
    URL.revokeObjectURL(link.href);
  }

  function bindActionButtons() {
    document.querySelectorAll('.print-btn').forEach(function (button) {
      button.addEventListener('click', function () {
        window.print();
      });
    });

    document.querySelectorAll('.export-btn').forEach(function (button) {
      button.addEventListener('click', function () {
        downloadReport();
        showToast('Report exported');
      });
    });

    document.querySelectorAll('.save-settings-btn').forEach(function (button) {
      button.addEventListener('click', function () {
        showToast('Changes saved locally');
      });
    });

    document.querySelectorAll('.upload-document-btn, .add-document-btn').forEach(function (button) {
      button.addEventListener('click', function () {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.pdf,.doc,.docx,.xls,.xlsx';
        input.addEventListener('change', function () {
          if (input.files.length > 0) showToast(input.files[0].name + ' selected');
        });
        input.click();
      });
    });

    document.querySelectorAll('.review-btn').forEach(function (button) {
      button.addEventListener('click', function () {
        showToast('Review panel opened');
      });
    });

    document.querySelectorAll('.manage-btn').forEach(function (button) {
      button.addEventListener('click', function () {
        const row = button.closest('tr');
        const name = row ? row.querySelector('strong').textContent : 'user';
        showToast('Managing ' + name);
      });
    });

    document.querySelectorAll('.profile-hero button').forEach(function (button) {
      button.addEventListener('click', function () {
        showToast('Photo picker opened');
      });
    });

    document.querySelectorAll('.thread-actions button').forEach(function (button) {
      button.addEventListener('click', function () {
        showToast('Thread options opened');
      });
    });
  }

  function bindDashboardLinks() {
    document.querySelectorAll('a[href="#"]').forEach(function (link) {
      link.addEventListener('click', function (event) {
        event.preventDefault();
        showToast(link.textContent.trim() + ' selected');
      });
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    bindSearches();
    bindFilterTabs();
    bindSelectableGroups();
    bindSettingsTabs();
    bindNotifications();
    bindMessaging();
    bindActionButtons();
    bindDashboardLinks();
  });
})();
