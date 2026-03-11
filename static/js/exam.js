/**
 * GED RLA EXAM ENGINE
 * Complete exam interface with timer, navigation, auto-save, and submit
 */

class GEDExam {
  constructor(config) {
    this.attemptId = config.attemptId;
    this.totalQuestions = config.totalQuestions;
    this.timeRemaining = config.timeRemaining;
    this.questions = config.questions;
    this.csrfToken = config.csrfToken;

    this.currentIndex = 0;
    this.answers = {};
    this.flagged = {};
    this.saveQueue = Promise.resolve();
    this.timerInterval = null;
    this.autoSaveInterval = null;
    this.isSubmitting = false;

    // Initialize from existing answers
    this.questions.forEach((q, idx) => {
      if (q.selected) {
        this.answers[q.id] = q.selected;
      }
      if (q.flagged) {
        this.flagged[q.id] = true;
      }
    });

    this.init();
  }

  init() {
    this.renderQuestion(this.currentIndex);
    this.renderPalette();
    this.startTimer();
    this.bindEvents();
    this.updateProgress();

    // Auto-save every 30 seconds
    this.autoSaveInterval = setInterval(() => this.saveCurrentAnswer(), 30000);

    // Warn before leaving
    window.addEventListener('beforeunload', (e) => {
      if (!this.isSubmitting) {
        e.preventDefault();
        e.returnValue = '';
      }
    });
  }

  startTimer() {
    this.timerInterval = setInterval(() => {
      this.timeRemaining--;
      this.updateTimerDisplay();
      if (this.timeRemaining <= 0) {
        clearInterval(this.timerInterval);
        this.autoSubmit();
      }
    }, 1000);
    this.updateTimerDisplay();
  }

  updateTimerDisplay() {
    const hours = Math.floor(this.timeRemaining / 3600);
    const minutes = Math.floor((this.timeRemaining % 3600) / 60);
    const seconds = this.timeRemaining % 60;

    const display = hours > 0
      ? `${hours}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
      : `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;

    const el = document.getElementById('timer-display');
    if (el) {
      el.textContent = display;
      el.className = 'timer-value';
      if (this.timeRemaining <= 300) el.classList.add('danger');
      else if (this.timeRemaining <= 900) el.classList.add('warning');
    }
  }

  renderQuestion(index) {
    const q = this.questions[index];
    if (!q) return;

    // Passage
    const passageContainer = document.getElementById('passage-container');
    if (passageContainer) {
      if (q.passage) {
        document.getElementById('passage-title').textContent = q.passage.title;
        document.getElementById('passage-meta').textContent =
          `${q.passage.author ? q.passage.author + ' · ' : ''}${q.passage.passage_type}`;
        const passageText = document.getElementById('passage-text');
        // Format passage content
        const paras = q.passage.content.split('\n\n');
        passageText.innerHTML = paras.map(p => `<p>${p.replace(/\n/g, ' ')}</p>`).join('');
        passageContainer.style.display = 'block';
      } else {
        passageContainer.style.display = 'none';
      }
    }

    // Question
    document.getElementById('question-num').textContent = `Question ${q.number} of ${this.totalQuestions}`;
    document.getElementById('question-skill').textContent = q.skill;
    document.getElementById('question-text').textContent = q.text;

    // Options
    const optionsEl = document.getElementById('options-list');
    optionsEl.innerHTML = '';
    q.options.forEach(opt => {
      const isSelected = this.answers[q.id] === opt.letter;
      const item = document.createElement('div');
      item.className = `option-item${isSelected ? ' selected' : ''}`;
      item.dataset.letter = opt.letter;
      item.innerHTML = `
        <div class="option-letter">${opt.letter}</div>
        <div class="option-text">${opt.text}</div>
      `;
      item.addEventListener('click', () => this.selectAnswer(opt.letter));
      optionsEl.appendChild(item);
    });

    // Flag button
    const flagBtn = document.getElementById('flag-btn');
    if (flagBtn) {
      const isFlagged = !!this.flagged[q.id];
      flagBtn.className = `flag-btn${isFlagged ? ' flagged' : ''}`;
      flagBtn.innerHTML = `<span>${isFlagged ? '🚩' : '⚑'}</span> ${isFlagged ? 'Flagged' : 'Flag for Review'}`;
    }

    // Navigation buttons
    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');
    if (prevBtn) prevBtn.disabled = index === 0;
    if (nextBtn) {
      nextBtn.textContent = index === this.totalQuestions - 1 ? 'Last Question' : 'Next →';
    }

    // Update palette current
    this.updatePaletteCurrent();
    this.updateAnsweredCount();
  }

  selectAnswer(letter) {
    const q = this.questions[this.currentIndex];
    this.answers[q.id] = letter;

    // Update UI
    document.querySelectorAll('.option-item').forEach(item => {
      item.classList.toggle('selected', item.dataset.letter === letter);
      const letterEl = item.querySelector('.option-letter');
      if (item.dataset.letter === letter) {
        letterEl.style.background = 'var(--accent-blue)';
        letterEl.style.borderColor = 'var(--accent-blue)';
        letterEl.style.color = 'white';
      } else {
        letterEl.style.background = '';
        letterEl.style.borderColor = '';
        letterEl.style.color = '';
      }
    });

    this.renderPalette();
    this.updateAnsweredCount();
    this.saveCurrentAnswer();
  }

  toggleFlag() {
    const q = this.questions[this.currentIndex];
    this.flagged[q.id] = !this.flagged[q.id];
    const flagBtn = document.getElementById('flag-btn');
    const isFlagged = this.flagged[q.id];
    flagBtn.className = `flag-btn${isFlagged ? ' flagged' : ''}`;
    flagBtn.innerHTML = `<span>${isFlagged ? '🚩' : '⚑'}</span> ${isFlagged ? 'Flagged' : 'Flag for Review'}`;
    this.renderPalette();
    this.saveCurrentAnswer();
  }

  goToQuestion(index) {
    if (index < 0 || index >= this.totalQuestions) return;
    this.saveCurrentAnswer();
    this.currentIndex = index;
    this.renderQuestion(index);
    // Scroll to top of question
    document.getElementById('question-card')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  renderPalette() {
    const palette = document.getElementById('question-palette');
    if (!palette) return;
    palette.innerHTML = '';

    this.questions.forEach((q, idx) => {
      const btn = document.createElement('button');
      btn.className = 'palette-btn';
      btn.textContent = idx + 1;

      if (idx === this.currentIndex) btn.classList.add('current');
      if (this.answers[q.id]) btn.classList.add('answered');
      if (this.flagged[q.id]) btn.classList.add('flagged');

      btn.addEventListener('click', () => this.goToQuestion(idx));
      palette.appendChild(btn);
    });
  }

  updatePaletteCurrent() {
    document.querySelectorAll('.palette-btn').forEach((btn, idx) => {
      btn.classList.toggle('current', idx === this.currentIndex);
    });
  }

  updateAnsweredCount() {
    const answered = Object.values(this.answers).filter(Boolean).length;
    const el = document.getElementById('answered-count');
    const el2 = document.getElementById('answered-count-sidebar');
    const html = `<strong>${answered}</strong> of ${this.totalQuestions} answered`;
    if (el) el.innerHTML = html;
    if (el2) el2.innerHTML = html;
  }

  updateProgress() {
    const answered = Object.values(this.answers).filter(Boolean).length;
    const pct = (answered / this.totalQuestions) * 100;
    const fill = document.getElementById('progress-fill');
    if (fill) fill.style.width = pct + '%';
    this.updateAnsweredCount();
  }

  saveCurrentAnswer() {
    const q = this.questions[this.currentIndex];
    const payload = {
      question_id: q.id,
      selected_answer: this.answers[q.id] || '',
      is_flagged: !!this.flagged[q.id],
      current_question: this.currentIndex + 1,
      time_remaining: this.timeRemaining,
    };

    this.saveQueue = this.saveQueue.then(() =>
      fetch(`/exam/save/${this.attemptId}/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': this.csrfToken,
        },
        body: JSON.stringify(payload),
      })
      .then(r => r.json())
      .catch(err => console.warn('Save failed:', err))
    );

    return this.saveQueue;
  }

  showSubmitModal() {
    const answered = Object.values(this.answers).filter(Boolean).length;
    const unanswered = this.totalQuestions - answered;
    const flaggedCount = Object.values(this.flagged).filter(Boolean).length;

    let warning = '';
    if (unanswered > 0) {
      warning += `<div style="color:var(--accent-orange);margin-bottom:8px;">⚠ ${unanswered} question${unanswered>1?'s':''} left unanswered</div>`;
    }
    if (flaggedCount > 0) {
      warning += `<div style="color:var(--accent-orange);margin-bottom:8px;">🚩 ${flaggedCount} question${flaggedCount>1?'s':''} flagged for review</div>`;
    }

    const modalBody = document.getElementById('modal-body');
    if (modalBody) {
      modalBody.innerHTML = `
        ${warning}
        <p>You have answered <strong style="color:var(--text-primary)">${answered}</strong> out of ${this.totalQuestions} questions.
        Once submitted, you cannot change your answers.</p>
      `;
    }

    document.getElementById('submit-modal').classList.add('active');
  }

  hideSubmitModal() {
    document.getElementById('submit-modal').classList.remove('active');
  }

  async confirmSubmit() {
    this.isSubmitting = true;
    clearInterval(this.timerInterval);
    clearInterval(this.autoSaveInterval);

    // Save current answer first
    await this.saveCurrentAnswer();

    const btn = document.getElementById('confirm-submit-btn');
    if (btn) {
      btn.disabled = true;
      btn.innerHTML = '<span class="spinner"></span> Submitting...';
    }

    try {
      const res = await fetch(`/exam/submit/${this.attemptId}/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': this.csrfToken,
        },
        body: JSON.stringify({ time_remaining: this.timeRemaining }),
      });
      const data = await res.json();
      if (data.redirect) {
        window.location.href = data.redirect;
      }
    } catch (err) {
      console.error('Submit failed:', err);
      if (btn) { btn.disabled = false; btn.textContent = 'Submit Test'; }
      this.isSubmitting = false;
    }
  }

  async autoSubmit() {
    this.isSubmitting = true;
    clearInterval(this.autoSaveInterval);
    await this.saveCurrentAnswer();

    document.getElementById('timer-display').textContent = '00:00';

    try {
      const res = await fetch(`/exam/submit/${this.attemptId}/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': this.csrfToken,
        },
        body: JSON.stringify({ time_remaining: 0 }),
      });
      const data = await res.json();
      if (data.redirect) window.location.href = data.redirect;
    } catch (err) {
      console.error('Auto-submit failed:', err);
    }
  }

  bindEvents() {
    // Navigation
    document.getElementById('prev-btn')?.addEventListener('click', () => {
      this.goToQuestion(this.currentIndex - 1);
    });

    document.getElementById('next-btn')?.addEventListener('click', () => {
      this.goToQuestion(this.currentIndex + 1);
    });

    // Flag
    document.getElementById('flag-btn')?.addEventListener('click', () => this.toggleFlag());

    // Submit
    document.getElementById('submit-btn')?.addEventListener('click', () => this.showSubmitModal());
    document.getElementById('cancel-submit')?.addEventListener('click', () => this.hideSubmitModal());
    document.getElementById('confirm-submit-btn')?.addEventListener('click', () => this.confirmSubmit());

    // Close modal on overlay click
    document.getElementById('submit-modal')?.addEventListener('click', (e) => {
      if (e.target === e.currentTarget) this.hideSubmitModal();
    });

    // Keyboard navigation
    document.addEventListener('keydown', (e) => {
      if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') this.goToQuestion(this.currentIndex - 1);
      if (e.key === 'ArrowRight' || e.key === 'ArrowDown') this.goToQuestion(this.currentIndex + 1);
      if (e.key >= '1' && e.key <= '4') {
        const letters = ['A', 'B', 'C', 'D'];
        this.selectAnswer(letters[parseInt(e.key) - 1]);
      }
    });
  }
}

// Results page: expandable review items
document.addEventListener('DOMContentLoaded', function() {
  document.querySelectorAll('.review-header').forEach(header => {
    header.addEventListener('click', () => {
      const item = header.closest('.review-item');
      item.classList.toggle('expanded');
    });
  });
});
