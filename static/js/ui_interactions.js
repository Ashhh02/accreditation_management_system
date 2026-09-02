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

  function bindNotificationMenu() {
    document.querySelectorAll('[data-notification-menu]').forEach(function (menu) {
      const trigger = menu.querySelector('[data-notification-trigger]');
      const popover = menu.querySelector('[data-notification-popover]');
      if (!trigger || !popover) return;

      function closePopover() {
        popover.hidden = true;
        trigger.setAttribute('aria-expanded', 'false');
      }

      trigger.addEventListener('click', function (event) {
        event.stopPropagation();
        const isOpen = !popover.hidden;
        popover.hidden = isOpen;
        trigger.setAttribute('aria-expanded', isOpen ? 'false' : 'true');
      });

      popover.addEventListener('click', function (event) {
        event.stopPropagation();
      });

      document.addEventListener('click', closePopover);
      document.addEventListener('keydown', function (event) {
        if (event.key === 'Escape') closePopover();
      });
    });
  }

  function getCookie(name) {
    const value = '; ' + String(document.cookie);
    const parts = value.split('; ' + name + '=');
    if (parts.length === 2) return parts.pop().split(';').shift();
    return '';
  }

  function requestJSON(url, options) {
    options = options || {};
    const headers = options.headers || {};
    if (options.body instanceof FormData) {
      headers['X-CSRFToken'] = getCookie('csrftoken');
    }
    return fetch(url, { credentials: 'same-origin', ...options, headers: headers })
      .then(function (response) {
        if (!response.ok) {
          return response.json()
            .catch(function () { return {}; })
            .then(function (payload) {
              const error = new Error(payload.error || 'Request failed');
              error.status = response.status;
              throw error;
            });
        }
        return response.json();
      });
  }

  function buildCompanionMessage(question) {
    const article = document.createElement('article');
    article.className = 'companion-user-message';
    const bubble = document.createElement('div');
    bubble.className = 'assistant-bubble';
    bubble.textContent = question;
    article.appendChild(bubble);
    return article;
  }

  function buildCompanionReply(text) {
    const article = document.createElement('article');
    article.className = 'companion-message companion-reply is-pending';
    article.innerHTML =
      '<div class="companion-bot-icon">' +
      '<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3v3M12 18v3M3 12h3M18 12h3M6 6l2 2M16 16l2 2M6 18l2-2M16 8l2-2"/><circle cx="12" cy="12" r="3"/></svg>' +
      '</div><div class="message-stack"><div class="assistant-bubble"></div></div>';
    article.querySelector('.assistant-bubble').textContent = text;
    return article;
  }

  function submitCompanionQuestion(input) {
    const question = input.value.trim();
    if (!question) {
      showToast('Choose a prompt or type a question');
      return;
    }

    const page = document.querySelector('[data-ask-url]');
    const replies = document.querySelector('.companion-replies');
    if (!page || !replies) return;

    const userMessage = buildCompanionMessage(question);
    const reply = buildCompanionReply('Thinking…');
    replies.appendChild(userMessage);
    replies.appendChild(reply);
    input.value = '';
    replies.scrollTop = replies.scrollHeight;

    const data = new FormData();
    data.append('question', question);
    requestJSON(page.dataset.askUrl, { method: 'POST', body: data })
      .then(function (payload) {
        const bubble = reply.querySelector('.assistant-bubble');
        bubble.classList.remove('is-pending');
        bubble.textContent = payload.answer || 'No answer available.';
        if (payload.sources?.length) {
          const sources = document.createElement('div');
          sources.className = 'companion-sources';
          payload.sources.forEach(function (source) {
            if (!source.url) return;
            const link = document.createElement('a');
            link.href = source.url;
            link.textContent = source.title;
            sources.appendChild(link);
          });
          reply.querySelector('.message-stack').appendChild(sources);
        }
        replies.scrollTop = replies.scrollHeight;
        showToast('AVA answered');
      })
      .catch(function (error) {
        const bubble = reply.querySelector('.assistant-bubble');
        bubble.classList.remove('is-pending');
        bubble.textContent = error.message || 'Something went wrong. Please try again.';
        showToast('Could not get an answer');
      });
  }

  function buildMessageRow(message) {
    const article = document.createElement('article');
    article.className = 'message-row' + (message.mine ? ' is-mine' : '') + (message.pending ? ' is-pending' : '');
    if (message.id) article.dataset.messageId = message.id;
    if (message.client_message_id) article.dataset.clientMessageId = message.client_message_id;
    if (!message.mine) {
      const author = document.createElement('div');
      author.className = 'message-author';
      author.textContent = message.author;
      const wrap = document.createElement('div');
      wrap.className = 'message-wrap';
      const avatar = document.createElement('span');
      avatar.className = 'message-avatar';
      avatar.textContent = message.initials;
      const inner = document.createElement('div');
      const bubble = document.createElement('div');
      bubble.className = 'message-bubble';
      bubble.textContent = message.text;
      const time = document.createElement('time');
      time.textContent = message.time;
      inner.appendChild(bubble);
      inner.appendChild(time);
      wrap.appendChild(avatar);
      wrap.appendChild(inner);
      article.appendChild(author);
      article.appendChild(wrap);
    } else {
      const bubble = document.createElement('div');
      bubble.className = 'message-bubble';
      bubble.textContent = message.text;
      const time = document.createElement('time');
      time.textContent = message.time;
      article.appendChild(bubble);
      article.appendChild(time);
    }
    return article;
  }

  function resolveChatContext() {
    const page = document.querySelector('[data-messages-api]');
    if (!page) return null;
    return {
      api: page.dataset.messagesApi,
      readUrl: page.dataset.readUrl || '',
      wsPath: page.dataset.wsPath || '/ws/communication/',
      conversation: page.dataset.activeConversation,
    };
  }

  const chatState = {
    socket: null,
    connected: false,
    reconnectTimer: null,
    reconnectDelay: 1000,
  };

  function chatSocketUrl(path) {
    const scheme = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
    return scheme + window.location.host + path;
  }

  function connectChatSocket() {
    const ctx = resolveChatContext();
    if (!ctx) return;
    const socket = new WebSocket(chatSocketUrl(ctx.wsPath));
    chatState.socket = socket;
    socket.addEventListener('open', onChatOpen);
    socket.addEventListener('message', onChatMessage);
    socket.addEventListener('close', onChatClose);
    socket.addEventListener('error', onChatError);
  }

  function onChatOpen() {
    chatState.connected = true;
    chatState.reconnectDelay = 1000;
    markActiveConversationRead();
  }

  function onChatClose() {
    chatState.connected = false;
    chatState.socket = null;
    window.clearTimeout(chatState.reconnectTimer);
    chatState.reconnectTimer = window.setTimeout(function () {
      connectChatSocket();
      chatState.reconnectDelay = Math.min(chatState.reconnectDelay * 2, 15000);
    }, chatState.reconnectDelay);
  }

  function onChatError() {
    chatState.connected = false;
  }

  function onChatMessage(event) {
    let data;
    try {
      data = JSON.parse(event.data);
    } catch (error) {
      return;
    }
    if (data.type === 'chat') {
      handleChatEvent(data.conversation_id, data.event, data.payload);
    } else if (data.type === 'connected') {
      markActiveConversationRead();
    } else if (data.type === 'error') {
      showToast(data.error || 'Communication error');
    }
  }

  function messageList() {
    return document.querySelector('.message-list');
  }

  function appendOrConfirmMessage(message) {
    const list = messageList();
    if (!list) return;
    const page = document.querySelector('[data-messages-api]');
    if (page?.dataset.currentUser && message.author_id) {
      message.mine = String(message.author_id) === String(page.dataset.currentUser);
      if (message.mine) {
        message.author = '';
        message.initials = '';
      }
    }
    if (message.id && list.querySelector('[data-message-id="' + message.id + '"]')) return;
    if (message.client_message_id) {
      const pending = list.querySelector('[data-client-message-id="' + message.client_message_id + '"]');
      if (pending) {
        pending.classList.remove('is-pending');
        if (message.id) pending.dataset.messageId = message.id;
        return;
      }
    }
    list.appendChild(buildMessageRow(message));
    list.scrollTop = list.scrollHeight;
  }

  function markActiveConversationRead() {
    const ctx = resolveChatContext();
    if (!ctx?.conversation) return;
    const active = document.querySelector('.conversation-item.is-active .conversation-badge');
    if (active) active.remove();
    if (chatState.connected && chatState.socket?.readyState === WebSocket.OPEN) {
      try {
        chatState.socket.send(JSON.stringify({ type: 'read', conversation_id: Number(ctx.conversation) }));
        return;
      } catch (error) {
        // fall through to the HTTP mark-read below
      }
    }
    if (!ctx.readUrl) return;
    const data = new FormData();
    data.append('conversation', ctx.conversation);
    requestJSON(ctx.readUrl, { method: 'POST', body: data }).catch(function () {});
  }

  function bumpConversationBadge(conversationId) {
    const item = document.querySelector('.conversation-item[data-conversation-id="' + conversationId + '"]');
    if (!item) return;
    const badge = item.querySelector('.conversation-badge');
    if (badge) {
      badge.textContent = (Number.parseInt(badge.textContent, 10) || 0) + 1;
    } else {
      const count = document.createElement('span');
      count.className = 'conversation-badge';
      count.textContent = '1';
      item.appendChild(count);
    }
  }

  function updateConversationPreview(conversationId, message) {
    const item = document.querySelector('.conversation-item[data-conversation-id="' + conversationId + '"]');
    if (!item) return;
    const preview = item.querySelector('.conversation-preview');
    const time = item.querySelector('.conversation-line em');
    if (preview) preview.textContent = message.text.slice(0, 90);
    if (time) time.textContent = message.time;
  }

  function handleChatEvent(conversationId, event, payload) {
    if (event !== 'message' || !payload?.message) return;
    const ctx = resolveChatContext();
    if (ctx && String(conversationId) === String(ctx.conversation)) {
      appendOrConfirmMessage(payload.message);
      if (!payload.message.mine) {
        markActiveConversationRead();
        updateConversationPreview(conversationId, payload.message);
      }
    } else {
      bumpConversationBadge(conversationId);
      updateConversationPreview(conversationId, payload.message);
    }
  }

  function postMessageHttp(ctx, text, clientMessageId) {
    const data = new FormData();
    data.append('conversation', ctx.conversation);
    data.append('body', text);
    data.append('client_message_id', clientMessageId);
    requestJSON(ctx.api, { method: 'POST', body: data })
      .then(function (payload) {
        const list = messageList();
        if (list) {
          const pending = list.querySelector('[data-client-message-id="' + clientMessageId + '"]');
          if (pending) {
            pending.classList.remove('is-pending');
            if (payload.id) pending.dataset.messageId = payload.id;
          }
        }
        showToast('Message sent');
      })
      .catch(function (error) {
        const list = messageList();
        if (list) {
          const pending = list.querySelector('[data-client-message-id="' + clientMessageId + '"]');
          if (pending) pending.remove();
        }
        showToast(error.message || 'Could not send message');
      });
  }

  function sendChatMessage(input) {
    const text = input.value.trim();
    if (!text) {
      showToast('Type a message first');
      return;
    }

    const ctx = resolveChatContext();
    const list = messageList();
    if (!ctx || !list) {
      showToast('Select a conversation first');
      return;
    }

    const clientMessageId = 'c' + Date.now().toString(36) + crypto.getRandomValues(new Uint32Array(1))[0].toString(36);
    const optimistic = {
      client_message_id: clientMessageId,
      text: text,
      time: 'Sending…',
      mine: true,
      pending: true,
    };
    list.appendChild(buildMessageRow(optimistic));
    input.value = '';
    list.scrollTop = list.scrollHeight;

    if (chatState.connected && chatState.socket?.readyState === WebSocket.OPEN) {
      try {
        chatState.socket.send(JSON.stringify({
          type: 'send_message',
          conversation_id: Number(ctx.conversation),
          body: text,
          client_message_id: clientMessageId,
        }));
        return;
      } catch (error) {
        // connection dropped mid-frame; fall back to HTTP below
      }
    }
    postMessageHttp(ctx, text, clientMessageId);
  }

  function bindMessaging() {
    document.querySelectorAll('.message-composer button').forEach(function (button) {
      button.addEventListener('click', function () {
        const input = button.closest('.message-composer').querySelector('input');
        sendChatMessage(input);
      });
    });

    document.querySelectorAll('.message-composer input').forEach(function (input) {
      input.addEventListener('keydown', function (event) {
        if (event.key === 'Enter') {
          event.preventDefault();
          sendChatMessage(input);
        }
      });
    });

    document.querySelectorAll('.conversation-item').forEach(function (item) {
      item.addEventListener('click', function () {
        const id = item.dataset.conversationId;
        const page = document.querySelector('[data-messages-api]');
        const list = messageList();
        if (!id || !page || !list) return;

        page.dataset.activeConversation = id;
        document.querySelectorAll('.conversation-item').forEach(function (other) {
          other.classList.toggle('is-active', other === item);
        });
        list.textContent = '';
        requestJSON(page.dataset.messagesApi + '?conversation=' + encodeURIComponent(id))
          .then(function (payload) {
            renderMessages(payload.messages, list);
            markActiveConversationRead();
          })
          .catch(function (error) {
            showToast(error.message);
          });
      });
    });

    document.querySelectorAll('.sample-prompt-list button').forEach(function (button) {
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
        submitCompanionQuestion(input);
      });
    });

    document.querySelectorAll('.composer-row input').forEach(function (input) {
      input.addEventListener('keydown', function (event) {
        if (event.key === 'Enter') {
          event.preventDefault();
          submitCompanionQuestion(input);
        }
      });
    });
  }

  function renderMessages(messages, list) {
    list.replaceChildren();
    messages.forEach(function (message) {
      list.appendChild(buildMessageRow(message));
    });
    list.scrollTop = list.scrollHeight;
  }

  function pollNotifications() {
    const menuRoot = document.querySelector('[data-notification-menu]');
    if (!menuRoot?.dataset.notificationFeedUrl) return;

    fetch(menuRoot.dataset.notificationFeedUrl, { credentials: 'same-origin' })
      .then(function (response) {
        return response.json();
      })
      .then(function (payload) {
        const trigger = menuRoot.querySelector('[data-notification-trigger]');
        const head = menuRoot.querySelector('.notification-popover-head span');
        const list = menuRoot.querySelector('.notification-popover-list');
        let badge = trigger ? trigger.querySelector('.dot-badge') : null;

        if (payload.unread > 0) {
          if (!badge) {
            badge = document.createElement('span');
            badge.className = 'dot-badge';
            if (trigger) trigger.appendChild(badge);
          }
          badge.textContent = payload.unread;
        } else if (badge) {
          badge.remove();
        }

        if (head) head.textContent = payload.unread + ' unread';
        if (list) {
          list.replaceChildren();
          if (!payload.items.length) {
            const empty = document.createElement('p');
            empty.className = 'notification-popover-empty';
            empty.textContent = 'No notifications yet.';
            list.appendChild(empty);
          } else {
            payload.items.forEach(function (item) {
              const link = document.createElement('a');
              link.href = item.submission_url || '#';
              link.className = 'notification-popover-item' + (item.unread ? ' is-unread' : '');
              link.innerHTML =
                '<span class="notification-popover-dot"></span>' +
                '<span class="notification-popover-copy"><strong></strong><small></small><em></em></span>';
              link.querySelector('strong').textContent = item.title;
              link.querySelector('small').textContent = item.message;
              link.querySelector('em').textContent = item.time_label;
              list.appendChild(link);
            });
          }
        }
      })
      .catch(function () {
        // ignore transient failures; next poll will retry
      });
  }

  function pollActiveConversationFallback() {
    const ctx = resolveChatContext();
    if (!ctx || chatState.connected) return;
    requestJSON(ctx.api + '?conversation=' + encodeURIComponent(ctx.conversation))
      .then(function (payload) {
        const list = messageList();
        if (!list) return;
        renderMessages(payload.messages, list);
        if (payload.unread > 0) markActiveConversationRead();
      })
      .catch(function () {
        // ignore transient failures; next poll will retry
      });
  }

  function applyProfilePhoto(photoUrl) {
    document.querySelectorAll('[data-profile-avatar]').forEach(function (avatar) {
      avatar.replaceChildren();
      if (photoUrl) {
        const image = document.createElement('img');
        image.className = 'avatar-photo';
        image.src = photoUrl;
        image.alt = 'Profile photo';
        avatar.appendChild(image);
        avatar.classList.add('has-photo');
      } else {
        avatar.classList.remove('has-photo');
        avatar.textContent = avatar.dataset.profileInitials || '';
      }
    });
  }

  function bindProfilePhoto() {
    const avatar = document.querySelector('[data-profile-avatar]');
    applyProfilePhoto(avatar ? avatar.dataset.profilePhoto || '' : '');

    const input = document.querySelector('#profile-photo-input');
    if (!input) return;

    document.querySelectorAll('.change-photo-btn').forEach(function (button) {
      button.addEventListener('click', function () {
        input.click();
      });
    });

    input.addEventListener('change', function () {
      const file = input.files && input.files[0];
      if (!file) return;

      if (!file.type.startsWith('image/')) {
        showToast('Choose an image file');
        input.value = '';
        return;
      }

      if (file.size > 5 * 1024 * 1024) {
        showToast('Photo must be smaller than 5 MB');
        input.value = '';
        return;
      }

      const reader = new FileReader();
      reader.addEventListener('load', function () {
        const photoUrl = typeof reader.result === 'string' ? reader.result : '';
        if (!photoUrl) return;

        applyProfilePhoto(photoUrl);
        showToast('Photo selected. Save changes to upload it.');
      });
      reader.addEventListener('error', function () {
        showToast('Could not read that photo');
        input.value = '';
      });
      reader.readAsDataURL(file);
    });
  }

  function bindActionButtons() {
    document.querySelectorAll('.print-btn').forEach(function (button) {
      button.addEventListener('click', function () {
        window.print();
      });
    });

    document.querySelectorAll('.save-settings-btn').forEach(function (button) {
      button.addEventListener('click', function () {
        showToast('Changes saved');
      });
    });

    document.querySelectorAll('.add-document-btn').forEach(function (button) {
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

    document.querySelectorAll('.thread-actions button').forEach(function (button) {
      button.addEventListener('click', function () {
        showToast('Thread options opened');
      });
    });
  }

  function bindWorkspaceActions() {
    // Workspace actions are regular server-backed forms. Keep this hook for
    // compatibility with the existing page initialisation sequence.
  }

  function toneForRole(role) {
    return {
      'Program Head': 'blue',
      Dean: 'rose',
      'Area Chair': 'gold',
      'Accreditation Head': 'maroon',
      QA: 'green',
    }[role] || 'slate';
  }

  function toneForStatus(status) {
    return status === 'Active' || status === 'Approved'
      ? 'green'
      : status === 'Pending'
        ? 'gold'
        : 'slate';
  }

  function bindUserManagement() {
    const dialog = document.querySelector('.user-manage-dialog');
    if (!dialog) return;

    const form = dialog.querySelector('.user-manage-form');
    let selectedButton = null;

    function closeDialog() {
      if (dialog.open) dialog.close();
      selectedButton = null;
    }

    document.querySelectorAll('.manage-btn').forEach(function (button) {
      button.addEventListener('click', function () {
        selectedButton = button;
        dialog.querySelector('[data-managed-name]').textContent = button.dataset.userName;
        dialog.querySelector('[data-managed-email]').textContent = button.dataset.userEmail;
        dialog.querySelector('.managed-user-avatar').textContent = button.dataset.userName
          .split(' ')
          .filter(function (part) { return !part.endsWith('.'); })
          .map(function (part) { return part.charAt(0); })
          .slice(-2)
          .join('');
        form.elements.role.value = button.dataset.userRole;
        form.elements.department.value = button.dataset.userDepartment;
        form.elements.status.value = button.dataset.userStatus;
        form.elements.approval.value = button.dataset.userApproval;
        dialog.showModal();
      });
    });

    dialog.querySelector('.dialog-close').addEventListener('click', closeDialog);
    dialog.querySelector('.dialog-cancel').addEventListener('click', closeDialog);
    dialog.addEventListener('click', function (event) {
      if (event.target === dialog) closeDialog();
    });

    form.addEventListener('submit', function (event) {
      event.preventDefault();
      if (!selectedButton) return;

      const row = selectedButton.closest('tr');
      const role = form.elements.role.value;
      const department = form.elements.department.value.trim();
      const status = form.elements.status.value;
      const approval = form.elements.approval.value;
      const userName = selectedButton.dataset.userName;

      selectedButton.dataset.userRole = role;
      selectedButton.dataset.userDepartment = department;
      selectedButton.dataset.userStatus = status;
      selectedButton.dataset.userApproval = approval;

      const roleChip = row.querySelector('td:nth-child(2) .user-chip');
      roleChip.textContent = role;
      roleChip.className = 'user-chip tone-' + toneForRole(role);
      row.querySelector('td:nth-child(3)').textContent = department;

      const statusChip = row.querySelector('.user-presence');
      statusChip.textContent = status;
      statusChip.className = 'user-presence tone-' + toneForStatus(status);

      const approvalChip = row.querySelector('td:nth-child(6) .user-chip');
      approvalChip.textContent = approval;
      approvalChip.className = 'user-chip tone-' + toneForStatus(approval);

      closeDialog();
      showToast(userName + ' updated');
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
    bindNotificationMenu();
    bindMessaging();
    connectChatSocket();
    window.setInterval(pollActiveConversationFallback, 20000);
    pollNotifications();
    window.setInterval(pollNotifications, 20000);
    bindProfilePhoto();
    bindActionButtons();
    bindWorkspaceActions();
    bindUserManagement();
    bindDashboardLinks();
  });
})();
