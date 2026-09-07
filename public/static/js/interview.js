document.addEventListener('DOMContentLoaded', () => {
  const app = document.getElementById('interview-app');
  if (!app) return;

  const role = app.dataset.role || 'General';
  let questions = [];
  try {
    questions = JSON.parse(app.dataset.questions || '[]');
  } catch (e) {
    questions = [];
  }

  if (!questions || questions.length === 0) return;

  const totalCount = questions.length;
  let currentIndex = 0;
  const scores = [];
  const sessionResults = [];

  // DOM Elements
  const questionTitle = document.getElementById('question-number-title');
  const questionCategory = document.getElementById('question-category-badge');
  const questionPrompt = document.getElementById('question-prompt');
  const answerTextarea = document.getElementById('answer');
  const wordCounter = document.getElementById('word-counter');
  const assessBtn = document.getElementById('assess-btn');
  const nextBtn = document.getElementById('next-question-btn');
  const progressFill = document.getElementById('interview-progress-fill');
  const runningScoreValue = document.getElementById('running-score-value');

  const questionSection = document.getElementById('question-section');
  const feedbackSection = document.getElementById('feedback-section');
  const summarySection = document.getElementById('summary-section');

  const questionScoreNum = document.getElementById('question-score-num');
  const questionScoreCircle = document.getElementById('question-score-circle');
  const feedbackSummaryTitle = document.getElementById('feedback-summary-title');
  const feedbackMainText = document.getElementById('feedback-main-text');
  const strengthsList = document.getElementById('feedback-strengths-list');
  const improvementsList = document.getElementById('feedback-improvements-list');

  const starBadges = {
    s: document.getElementById('star-badge-s'),
    t: document.getElementById('star-badge-t'),
    a: document.getElementById('star-badge-a'),
    r: document.getElementById('star-badge-r'),
  };

  // Word counter handler
  if (answerTextarea && wordCounter) {
    answerTextarea.addEventListener('input', () => {
      const words = answerTextarea.value.trim().split(/\s+/).filter(Boolean).length;
      wordCounter.textContent = `${words} words (aim for 90–180)`;
      if (words < 40) {
        wordCounter.style.color = 'var(--muted)';
      } else if (words >= 70 && words <= 240) {
        wordCounter.style.color = '#087f5b';
      } else {
        wordCounter.style.color = '#f76707';
      }
    });
  }

  // Load specific question into the UI
  function loadQuestion(index) {
    const q = questions[index];
    const category = typeof q === 'object' ? q.category : 'Interview Drill';
    const text = typeof q === 'object' ? q.text : q;

    if (questionTitle) questionTitle.textContent = `Question ${index + 1} of ${totalCount}`;
    if (questionCategory) questionCategory.textContent = category;
    if (questionPrompt) questionPrompt.textContent = text;
    if (answerTextarea) {
      answerTextarea.value = '';
      answerTextarea.focus();
    }
    if (wordCounter) {
      wordCounter.textContent = '0 words (aim for 90–180)';
      wordCounter.style.color = 'var(--muted)';
    }

    // Update Progress bar
    if (progressFill) {
      const pct = Math.round(((index + 1) / totalCount) * 100);
      progressFill.style.width = `${pct}%`;
    }

    // Update Question pills status
    for (let i = 0; i < totalCount; i++) {
      const pill = document.getElementById(`q-pill-${i}`);
      if (pill) {
        pill.classList.remove('q-pill-active');
        if (i === index) {
          pill.classList.add('q-pill-active');
        }
      }
    }

    if (questionSection) questionSection.style.display = 'block';
    if (feedbackSection) feedbackSection.style.display = 'none';
  }

  // Submit and Assess Answer
  if (assessBtn) {
    assessBtn.addEventListener('click', async () => {
      const answer = answerTextarea.value.trim();
      if (!answer) {
        alert('Please write an answer before requesting feedback.');
        answerTextarea.focus();
        return;
      }

      assessBtn.disabled = true;
      assessBtn.textContent = 'Analyzing with STAR rubric...';

      const currentQ = questions[currentIndex];
      const qText = typeof currentQ === 'object' ? currentQ.text : currentQ;
      const qCat = typeof currentQ === 'object' ? currentQ.category : 'General';

      try {
        const res = await fetch('/interview/assess', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ answer, question: qText }),
        });
        const result = await res.json();

        scores.push(result.score);
        sessionResults.push({
          question: qText,
          category: qCat,
          score: result.score,
          answer: answer,
          feedback: result.feedback,
        });

        // Update current pill with score
        const pill = document.getElementById(`q-pill-${currentIndex}`);
        const pillScore = document.getElementById(`q-pill-score-${currentIndex}`);
        if (pill) {
          pill.classList.remove('q-pill-active', 'q-pill-pending');
          pill.classList.add('q-pill-done');
        }
        if (pillScore) {
          pillScore.textContent = `${result.score}%`;
        }

        // Calculate and update running score
        const runningAvg = Math.round(scores.reduce((a, b) => a + b, 0) / scores.length);
        if (runningScoreValue) runningScoreValue.textContent = runningAvg;

        // Populate feedback card
        if (questionScoreNum) questionScoreNum.textContent = result.score;
        if (feedbackSummaryTitle) {
          if (result.score >= 80) feedbackSummaryTitle.textContent = '🌟 Strong Response';
          else if (result.score >= 65) feedbackSummaryTitle.textContent = '👍 Good Answer';
          else feedbackSummaryTitle.textContent = '⚠️ Needs More Structure';
        }
        if (feedbackMainText) feedbackMainText.textContent = result.feedback;

        // STAR Badges
        if (result.star) {
          Object.keys(starBadges).forEach((key) => {
            const badge = starBadges[key];
            if (badge) {
              const fullKey = key === 's' ? 'situation' : key === 't' ? 'task' : key === 'a' ? 'action' : 'result';
              if (result.star[fullKey]) {
                badge.className = 'star-badge star-badge-active';
                badge.textContent = `✓ ${badge.textContent.replace(/^([✓+]\s*)?/, '')}`;
              } else {
                badge.className = 'star-badge star-badge-missing';
                badge.textContent = `+ ${badge.textContent.replace(/^([✓+]\s*)?/, '')}`;
              }
            }
          });
        }

        // Strengths & Improvements
        if (strengthsList) {
          strengthsList.innerHTML = (result.strengths || []).map((s) => `<li>${s}</li>`).join('');
        }
        if (improvementsList) {
          improvementsList.innerHTML = (result.improvements || []).map((i) => `<li>${i}</li>`).join('');
        }

        // Configure next button
        if (nextBtn) {
          if (currentIndex < totalCount - 1) {
            nextBtn.textContent = 'Next Question →';
          } else {
            nextBtn.textContent = 'Complete Interview & View Scorecard 🏆';
          }
        }

        // Show feedback
        if (feedbackSection) {
          feedbackSection.style.display = 'block';
          feedbackSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      } catch (err) {
        alert('An error occurred during assessment. Please try again.');
      } finally {
        assessBtn.disabled = false;
        assessBtn.textContent = 'Submit Answer for AI Review';
      }
    });
  }

  // Next Question / Finish handler
  if (nextBtn) {
    nextBtn.addEventListener('click', () => {
      if (currentIndex < totalCount - 1) {
        currentIndex++;
        loadQuestion(currentIndex);
        window.scrollTo({ top: 0, behavior: 'smooth' });
      } else {
        finishInterview();
      }
    });
  }

  // Final summary completion handler
  async function finishInterview() {
    const overallAvg = Math.round(scores.reduce((a, b) => a + b, 0) / scores.length);

    // Save session activity
    try {
      await fetch('/interview/complete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ overall_score: overallAvg, question_count: totalCount }),
      });
    } catch (e) {
      console.warn('Could not record interview completion activity:', e);
    }

    // Populate scorecard
    const finalScoreNum = document.getElementById('final-score-num');
    const finalRatingLabel = document.getElementById('final-rating-label');
    const tableBody = document.getElementById('progression-table-body');

    if (finalScoreNum) finalScoreNum.textContent = overallAvg;
    if (finalRatingLabel) {
      if (overallAvg >= 82) finalRatingLabel.textContent = 'Ready for Real Interviews! 🔥';
      else if (overallAvg >= 68) finalRatingLabel.textContent = 'Solid Performance — Polish metrics to stand out';
      else finalRatingLabel.textContent = 'Good Practice Run — Emphasize the STAR format';
    }

    if (tableBody) {
      tableBody.innerHTML = sessionResults
        .map(
          (r, idx) => `
        <tr style="border-bottom: 1px solid var(--line);">
          <td style="padding: 12px 10px;">
            <strong>Q${idx + 1}:</strong> ${r.question.slice(0, 65)}...
          </td>
          <td style="padding: 12px 10px;">
            <span class="badge" style="background:#eef2ff; color:#4f46e5;">${r.category}</span>
          </td>
          <td style="padding: 12px 10px; text-align: right; font-weight: 800; color: ${r.score >= 75 ? '#087f5b' : r.score >= 60 ? 'var(--accent)' : '#f76707'};">
            ${r.score}%
          </td>
        </tr>
      `
        )
        .join('');
    }

    if (questionSection) questionSection.style.display = 'none';
    if (feedbackSection) feedbackSection.style.display = 'none';
    const headerCard = document.querySelector('.interview-header-card');
    if (headerCard) headerCard.style.display = 'none';

    if (summarySection) {
      summarySection.style.display = 'block';
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  }

  // Initialize with question 0
  loadQuestion(0);
});
