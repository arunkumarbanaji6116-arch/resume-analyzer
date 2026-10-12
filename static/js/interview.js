document.addEventListener('DOMContentLoaded', () => {
  const app = document.getElementById('interview-app');
  if (!app) return;

  const role = app.dataset.role || 'General';
  const selectedVoice = app.dataset.voice || 'arun';
  const autoSpeak = app.dataset.autoSpeak === 'true';
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

  // Voice Interviewer State
  let isMuted = false;
  let isSpeaking = false;
  let currentAudio = null;
  let currentAudioUrl = null;
  let currentUtterance = null;

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
  const feedbackSummaryTitle = document.getElementById('feedback-summary-title');
  const feedbackMainText = document.getElementById('feedback-main-text');
  const strengthsList = document.getElementById('feedback-strengths-list');
  const improvementsList = document.getElementById('feedback-improvements-list');

  // Voice UI Elements
  const voiceAvatar = document.getElementById('voice-avatar');
  const soundWaveBars = document.getElementById('sound-wave-bars');
  const voiceStatusText = document.getElementById('voice-status-text');
  const replayVoiceBtn = document.getElementById('replay-voice-btn');
  const muteVoiceBtn = document.getElementById('mute-voice-btn');
  const muteIconUnmuted = document.getElementById('mute-icon-unmuted');
  const muteIconMuted = document.getElementById('mute-icon-muted');
  const replayBtnLabel = document.getElementById('replay-btn-label');

  const starBadges = {
    s: document.getElementById('star-badge-s'),
    t: document.getElementById('star-badge-t'),
    a: document.getElementById('star-badge-a'),
    r: document.getElementById('star-badge-r'),
  };

  const interviewType = app.dataset.interviewType || 'star';
  const isMcq = interviewType === 'mcq';

  // MCQ UI Elements
  const starAnswerBlock = document.getElementById('star-answer-block');
  const mcqAnswerBlock = document.getElementById('mcq-answer-block');
  const mcqOptionsGrid = document.getElementById('mcq-options-grid');
  const starFeedbackDetails = document.getElementById('star-feedback-details');
  const mcqFeedbackDetails = document.getElementById('mcq-feedback-details');
  const mcqExplanationText = document.getElementById('mcq-explanation-text');

  let selectedOptionId = null;
  let isAssessed = false;

  // Custom Spatial Modal Dialog Elements
  const interviewModal = document.getElementById('interview-modal');
  const modalTitle = document.getElementById('interview-modal-title');
  const modalDesc = document.getElementById('interview-modal-desc');
  const modalIcon = document.getElementById('interview-modal-icon');
  const modalConfirmBtn = document.getElementById('interview-modal-confirm-btn');
  const modalCloseBtn = document.getElementById('interview-modal-close-btn');

  function showInterviewModal({ title = 'Attention', message = '', icon = '🎯', onConfirm = null } = {}) {
    if (!interviewModal) {
      alert(message);
      return;
    }
    if (modalTitle) modalTitle.textContent = title;
    if (modalDesc) modalDesc.textContent = message;
    if (modalIcon) modalIcon.textContent = icon;

    interviewModal.style.display = 'flex';
    interviewModal.classList.remove('closing');

    if (modalConfirmBtn) {
      modalConfirmBtn.focus();
      modalConfirmBtn.onclick = () => {
        closeInterviewModal();
        if (typeof onConfirm === 'function') onConfirm();
      };
    }
  }

  function closeInterviewModal() {
    if (!interviewModal) return;
    interviewModal.classList.add('closing');
    setTimeout(() => {
      interviewModal.style.display = 'none';
      interviewModal.classList.remove('closing');
    }, 180);
  }

  if (modalCloseBtn) {
    modalCloseBtn.addEventListener('click', closeInterviewModal);
  }

  if (interviewModal) {
    interviewModal.addEventListener('click', (e) => {
      if (e.target === interviewModal) {
        closeInterviewModal();
      }
    });
  }

  window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && interviewModal && interviewModal.style.display === 'flex') {
      closeInterviewModal();
    }
  });

  // Pre-load browser voices if available
  if ('speechSynthesis' in window && window.speechSynthesis.onvoiceschanged !== undefined) {
    window.speechSynthesis.onvoiceschanged = () => {
      window.speechSynthesis.getVoices();
    };
  }

  // Stop all playing audio & speech synthesis
  function stopAllAudio() {
    if (currentAudio) {
      try {
        currentAudio.pause();
        currentAudio.currentTime = 0;
      } catch (e) {}
      currentAudio = null;
    }
    if (currentAudioUrl) {
      try {
        URL.revokeObjectURL(currentAudioUrl);
      } catch (e) {}
      currentAudioUrl = null;
    }
    if ('speechSynthesis' in window && window.speechSynthesis.speaking) {
      try {
        window.speechSynthesis.cancel();
      } catch (e) {}
    }
    currentUtterance = null;
    setSpeakingUI(false);
  }

  // Update UI reflecting speaking vs listening state
  function setSpeakingUI(speaking, customStatus) {
    isSpeaking = speaking;
    if (speaking) {
      if (voiceAvatar) voiceAvatar.classList.add('speaking');
      if (soundWaveBars) soundWaveBars.classList.add('active');
      if (voiceStatusText) voiceStatusText.textContent = customStatus || '🎙️ AI Interviewer Asking Question...';
      if (replayBtnLabel) replayBtnLabel.textContent = 'Speaking...';
      if (replayVoiceBtn) replayVoiceBtn.classList.add('active');
    } else {
      if (voiceAvatar) voiceAvatar.classList.remove('speaking');
      if (soundWaveBars) soundWaveBars.classList.remove('active');
      if (voiceStatusText) {
        voiceStatusText.textContent = customStatus || (isMuted ? '🔇 Audio muted' : 'Ready to ask question');
      }
      if (replayBtnLabel) replayBtnLabel.textContent = 'Replay Question';
      if (replayVoiceBtn) replayVoiceBtn.classList.remove('active');
    }
  }

  // Fallback speech synthesis when ElevenLabs is unavailable
  function fallbackBrowserSpeech(text, onEnd) {
    if (isMuted || !('speechSynthesis' in window)) {
      if (onEnd) onEnd();
      return;
    }

    try {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);

      // Pitch & rate tailored to persona (Arun, Shravan, Rakesh, Sai Srinath)
      if (selectedVoice === 'sai_srinath' || selectedVoice === 'george') {
        utterance.pitch = 0.85;
        utterance.rate = 0.92;
      } else if (selectedVoice === 'shravan' || selectedVoice === 'adam') {
        utterance.pitch = 0.88;
        utterance.rate = 0.96;
      } else if (selectedVoice === 'rakesh' || selectedVoice === 'sarah') {
        utterance.pitch = 1.0;
        utterance.rate = 1.0;
      } else {
        // arun (default)
        utterance.pitch = 0.95;
        utterance.rate = 0.98;
      }

      const voices = window.speechSynthesis.getVoices();
      if (voices && voices.length > 0) {
        // All team members (Arun, Shravan, Rakesh, Sai Srinath) are male
        const isMale = true;
        const targetVoice =
          voices.find((v) => {
            const name = (v.name || '').toLowerCase();
            const lang = (v.lang || '').toLowerCase();
            if (!lang.startsWith('en')) return false;
            if (isMale) {
              return (
                name.includes('male') ||
                name.includes('david') ||
                name.includes('george') ||
                name.includes('guy') ||
                name.includes('james') ||
                name.includes('mark') ||
                name.includes('ravi') ||
                name.includes('prabhat')
              );
            }
            return (
              name.includes('female') ||
              name.includes('zira') ||
              name.includes('samantha') ||
              name.includes('natural')
            );
          }) ||
          voices.find((v) => (v.lang || '').toLowerCase().startsWith('en')) ||
          voices[0];

        if (targetVoice) utterance.voice = targetVoice;
      }

      utterance.onend = () => {
        currentUtterance = null;
        if (onEnd) onEnd();
      };
      utterance.onerror = () => {
        currentUtterance = null;
        if (onEnd) onEnd();
      };

      currentUtterance = utterance;
      window.speechSynthesis.speak(utterance);
    } catch (e) {
      console.warn('Speech synthesis playback failed:', e);
      if (onEnd) onEnd();
    }
  }

  // Zero-latency voice playback (< 5ms start) using browser native speech synthesis
  function speakQuestion(text) {
    if (!text || isMuted) return;
    stopAllAudio();
    setSpeakingUI(true, '🎙️ AI Interviewer Asking Question...');

    fallbackBrowserSpeech(text, () => {
      setSpeakingUI(false, '🎧 Listening for your response');
    });
  }

  // STAR Rubric Keywords for Zero-Latency live detection & evaluation (< 0.1ms)
  const STAR_KEYWORDS = {
    situation: [
      "situation", "context", "background", "when", "company", "project", "client", "team", "working at", "faced",
      "problem", "issue", "bug", "outage", "incident", "crash", "downtime", "failure", "error", "bottleneck",
      "customer", "user", "legacy", "system", "app", "service", "production", "environment", "during", "while", "scenario"
    ],
    task: [
      "task", "goal", "target", "needed to", "had to", "wanted to", "responsible for", "objective", "challenge",
      "assigned", "requirement", "tasked with", "my role", "priority", "mandate", "decided to", "in order to"
    ],
    action: [
      "built", "designed", "developed", "wrote", "coded", "implemented", "refactored", "analyzed", "coordinated",
      "resolved", "spearheaded", "executed", "optimized", "configured", "deployed", "migrated", "investigated",
      "debugged", "fixed", "solved", "created", "architected", "automated", "tuned", "indexed", "integrated", "tested", "led"
    ],
    result: [
      "result", "impact", "increased", "decreased", "reduced", "improved", "saved", "%", "percent", "metric",
      "revenue", "achieved", "learned", "outcome", "boosted", "accelerated", "dropped", "doubled", "tripled",
      "eliminated", "uptime", "latency", "throughput", "performance", "ms", "seconds", "hours", "success", "smoothly"
    ]
  };

  const liveStarS = document.getElementById('live-star-s');
  const liveStarT = document.getElementById('live-star-t');
  const liveStarA = document.getElementById('live-star-a');
  const liveStarR = document.getElementById('live-star-r');

  function updateLiveStarIndicators(text) {
    if (!text) {
      if (liveStarS) liveStarS.className = 'live-star-badge';
      if (liveStarT) liveStarT.className = 'live-star-badge';
      if (liveStarA) liveStarA.className = 'live-star-badge';
      if (liveStarR) liveStarR.className = 'live-star-badge';
      return;
    }
    const tLower = text.toLowerCase();
    const hasS = STAR_KEYWORDS.situation.some(k => tLower.includes(k));
    const hasT = STAR_KEYWORDS.task.some(k => tLower.includes(k));
    const hasA = STAR_KEYWORDS.action.some(k => tLower.includes(k));
    const hasR = STAR_KEYWORDS.result.some(k => tLower.includes(k)) || /\b\d+[%+]?\b/.test(text);

    if (liveStarS) liveStarS.className = 'live-star-badge ' + (hasS ? 'detected' : '');
    if (liveStarT) liveStarT.className = 'live-star-badge ' + (hasT ? 'detected' : '');
    if (liveStarA) liveStarA.className = 'live-star-badge ' + (hasA ? 'detected' : '');
    if (liveStarR) liveStarR.className = 'live-star-badge ' + (hasR ? 'detected' : '');
  }

  function isGibberish(text) {
    const clean = (text || '').replace(/[^a-zA-Z\s]/g, '').trim();
    if (!clean || clean.length < 3) return true;
    const words = clean.split(/\s+/);
    if (words.length === 1) {
      const w = words[0].toLowerCase();
      if (w.length >= 4 && !/[aeiouy]/.test(w)) return true;
      if (new Set(['asdf', 'asdfghjk', 'asdfqhjk', 'qwerty', 'zxcv', 'test', 'testing']).has(w)) return true;
    }
    return false;
  }

  function evaluateStarLocally(text) {
    const trimmed = (text || '').trim();
    const words = trimmed.toLowerCase().match(/\b[\w+#.-]+\b/g) || [];
    const wordCount = words.length;

    if (isGibberish(trimmed) || wordCount < 2) {
      return {
        score: 20,
        word_count: wordCount,
        star: { situation: false, task: false, action: false, result: false },
        strengths: [],
        improvements: [
          "Structure your response using the STAR method: Situation, Task, Action, and Result.",
          "Describe a real engineering or workplace experience with specific tools and measurable outcomes."
        ],
        feedback: "Your input appears to be test or random characters. Please describe a genuine professional experience using the STAR method to receive an accurate evaluation."
      };
    }

    const textLower = trimmed.toLowerCase();
    const hasSituation = STAR_KEYWORDS.situation.some(k => textLower.includes(k));
    const hasTask = STAR_KEYWORDS.task.some(k => textLower.includes(k));
    const hasAction = STAR_KEYWORDS.action.some(k => textLower.includes(k));
    const hasResult = STAR_KEYWORDS.result.some(k => textLower.includes(k)) || /\b\d+[%+]?\b/.test(trimmed);

    const starCount = (hasSituation ? 1 : 0) + (hasTask ? 1 : 0) + (hasAction ? 1 : 0) + (hasResult ? 1 : 0);

    let score = 70 + (starCount * 6);
    if (wordCount < 8) score = 35 + (starCount * 8);
    else if (wordCount < 20) score = 48 + (starCount * 8);
    else if (wordCount < 40) score = 56 + (starCount * 8);
    else if (wordCount < 80) score = 64 + (starCount * 7);

    const metricsMatches = trimmed.match(/\b\d+(?:\.\d+)?%?\b/g) || [];
    if (metricsMatches.length >= 2) score += 8;
    else if (metricsMatches.length === 1) score += 5;

    score = Math.min(98, Math.max(25, score));

    const strengths = [];
    const improvements = [];

    if (hasAction) strengths.push("Demonstrated clear personal ownership with active engineering verbs.");
    if (hasResult || metricsMatches.length > 0) strengths.push("Included concrete results or measurable performance impact.");
    if (hasSituation || hasTask) strengths.push("Provided clear project background and defined responsibilities.");
    if (strengths.length === 0) strengths.push("Directly addressed the interview question.");

    if (!hasResult) improvements.push("Quantify the final outcome (e.g. % latency decrease, uptime metric, revenue saved).");
    if (!hasSituation) improvements.push("Set the scene by briefly describing the company, team, or problem context.");
    if (!hasTask) improvements.push("Clarify your specific role or challenge within the project.");
    if (wordCount < 40) improvements.push("Elaborate on the technical trade-offs and decision rationale you considered.");
    else if (wordCount > 300) improvements.push("Keep your answer concise (aim for ~90-180 words) to avoid rambling.");

    let feedback = "Good foundation. Elaborate on the context and measurable results using the STAR framework.";
    if (score >= 80) feedback = "Outstanding response! Strong STAR structure, concrete engineering actions, and impactful outcome.";
    else if (score >= 65) feedback = "Solid answer. Strengthen with deeper context on the problem and specific measurable metrics.";

    return {
      score,
      word_count: wordCount,
      star: {
        situation: hasSituation,
        task: hasTask,
        action: hasAction,
        result: hasResult
      },
      strengths,
      improvements: improvements.length ? improvements : ["Continue practicing for fluid, confident delivery."],
      feedback
    };
  }

  // Real-time word counter & Live STAR indicator handler (Zero-Latency)
  if (answerTextarea && wordCounter) {
    answerTextarea.addEventListener('input', () => {
      const val = answerTextarea.value;
      const words = val.trim().split(/\s+/).filter(Boolean).length;
      wordCounter.textContent = `${words} words (aim for 90–180)`;
      if (words < 40) {
        wordCounter.style.color = 'var(--muted)';
      } else if (words >= 70 && words <= 240) {
        wordCounter.style.color = '#087f5b';
      } else {
        wordCounter.style.color = '#f76707';
      }
      updateLiveStarIndicators(val);
    });
  }

  // Load specific question into the UI
  function loadQuestion(index) {
    if (index < 0 || index >= totalCount) return;
    currentIndex = index;
    isAssessed = false;
    selectedOptionId = null;
    stopAllAudio();

    const q = questions[index];
    const category = typeof q === 'object' ? q.category : 'Interview Drill';
    const text = typeof q === 'object' ? q.text : q;

    if (questionTitle) questionTitle.textContent = `Question ${index + 1} of ${totalCount}`;
    if (questionCategory) questionCategory.textContent = category;
    if (questionPrompt) questionPrompt.textContent = text;

    if (isMcq) {
      if (starAnswerBlock) starAnswerBlock.style.display = 'none';
      if (mcqAnswerBlock) mcqAnswerBlock.style.display = 'block';
      if (starFeedbackDetails) starFeedbackDetails.style.display = 'none';
      if (mcqFeedbackDetails) mcqFeedbackDetails.style.display = 'block';
      if (assessBtn) {
        assessBtn.textContent = 'Submit Option for Instant Review';
        assessBtn.disabled = false;
      }

      // Render options dynamically
      if (mcqOptionsGrid) {
        mcqOptionsGrid.innerHTML = '';
        const options = q.options || [];
        options.forEach((opt) => {
          const card = document.createElement('div');
          card.className = 'mcq-option-card';
          card.dataset.optionId = opt.id;
          card.innerHTML = `
            <span class="mcq-option-letter">${opt.id}</span>
            <span class="mcq-option-text">${opt.text}</span>
          `;
          card.addEventListener('click', () => {
            if (isAssessed) return;
            const allCards = mcqOptionsGrid.querySelectorAll('.mcq-option-card');
            allCards.forEach((c) => c.classList.remove('selected'));
            card.classList.add('selected');
            selectedOptionId = opt.id;
          });
          mcqOptionsGrid.appendChild(card);
        });
      }
    } else {
      if (starAnswerBlock) starAnswerBlock.style.display = 'block';
      if (mcqAnswerBlock) mcqAnswerBlock.style.display = 'none';
      if (starFeedbackDetails) starFeedbackDetails.style.display = 'block';
      if (mcqFeedbackDetails) mcqFeedbackDetails.style.display = 'none';
      if (assessBtn) {
        assessBtn.textContent = 'Submit Answer for AI Review';
        assessBtn.disabled = false;
      }

      if (answerTextarea) {
        answerTextarea.value = '';
        answerTextarea.focus();
      }
      if (wordCounter) {
        wordCounter.textContent = '0 words (aim for 90–180)';
        wordCounter.style.color = 'var(--muted)';
      }
      updateLiveStarIndicators('');
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

    // Auto speak question if enabled
    if (autoSpeak && !isMuted) {
      setTimeout(() => {
        speakQuestion(text);
      }, 350);
    } else {
      setSpeakingUI(false, isMuted ? '🔇 Audio muted' : 'Ready to ask question');
    }
  }

  // Replay Question button handler
  if (replayVoiceBtn) {
    replayVoiceBtn.addEventListener('click', () => {
      const currentQ = questions[currentIndex];
      const text = typeof currentQ === 'object' ? currentQ.text : currentQ;

      if (isSpeaking) {
        stopAllAudio();
      } else {
        if (isMuted) {
          isMuted = false;
          if (muteIconUnmuted) muteIconUnmuted.style.display = 'inline';
          if (muteIconMuted) muteIconMuted.style.display = 'none';
          if (muteVoiceBtn) muteVoiceBtn.classList.remove('muted');
        }
        speakQuestion(text);
      }
    });
  }

  // Mute / Unmute button handler
  if (muteVoiceBtn) {
    muteVoiceBtn.addEventListener('click', () => {
      isMuted = !isMuted;
      if (isMuted) {
        stopAllAudio();
        if (muteIconUnmuted) muteIconUnmuted.style.display = 'none';
        if (muteIconMuted) muteIconMuted.style.display = 'inline';
        muteVoiceBtn.classList.add('muted');
        if (voiceStatusText) voiceStatusText.textContent = '🔇 Audio muted';
      } else {
        if (muteIconUnmuted) muteIconUnmuted.style.display = 'inline';
        if (muteIconMuted) muteIconMuted.style.display = 'none';
        muteVoiceBtn.classList.remove('muted');
        if (voiceStatusText) voiceStatusText.textContent = 'Ready to ask question';
      }
    });
  }

  // Submit and Assess Answer (Zero-Latency Engine: Instant 0ms local evaluation + background sync)
  if (assessBtn) {
    assessBtn.addEventListener('click', () => {
      stopAllAudio();

      const currentQ = questions[currentIndex];
      const qText = typeof currentQ === 'object' ? currentQ.text : currentQ;
      const qCat = typeof currentQ === 'object' ? currentQ.category : 'General';

      if (isMcq) {
        if (!selectedOptionId) {
          showInterviewModal({
            title: 'Select an Option',
            message: 'Please select one of the options (A, B, C, or D) before submitting.',
            icon: '🎯'
          });
          return;
        }

        // Instant Zero-Latency MCQ Evaluation (0ms)
        const isCorrect = (selectedOptionId || '').trim().toUpperCase() === (currentQ.correct || '').trim().toUpperCase();
        const score = isCorrect ? 100 : 0;
        const explanation = currentQ.explanation || '';
        const feedback = isCorrect
          ? 'Outstanding! You chose the optimal engineering solution.'
          : `Incorrect. The optimal answer was Option ${currentQ.correct}.`;

        isAssessed = true;
        assessBtn.disabled = true;
        assessBtn.textContent = 'Answer Evaluated ✓';

        // Highlight correct and wrong options immediately (0ms)
        if (mcqOptionsGrid) {
          const allCards = mcqOptionsGrid.querySelectorAll('.mcq-option-card');
          allCards.forEach((card) => {
            card.classList.add('disabled');
            if (card.dataset.optionId === currentQ.correct) {
              card.classList.add('correct');
            }
            if (!isCorrect && card.dataset.optionId === selectedOptionId) {
              card.classList.add('wrong');
            }
          });
        }

        scores.push(score);
        sessionResults.push({
          question: qText,
          category: qCat,
          score: score,
          is_correct: isCorrect,
          selected_option: selectedOptionId,
          correct_option: currentQ.correct,
          explanation: explanation
        });

        // Update current pill with score immediately
        const pill = document.getElementById(`q-pill-${currentIndex}`);
        const pillScore = document.getElementById(`q-pill-score-${currentIndex}`);
        if (pill) {
          pill.classList.remove('q-pill-active', 'q-pill-pending');
          pill.classList.add('q-pill-done');
        }
        if (pillScore) {
          pillScore.textContent = `${score}%`;
        }

        // Calculate and update running score immediately
        const runningAvg = Math.round(scores.reduce((a, b) => a + b, 0) / scores.length);
        if (runningScoreValue) runningScoreValue.textContent = runningAvg;

        // Populate feedback card
        if (questionScoreNum) questionScoreNum.textContent = score;
        const scoreCircle = document.getElementById('question-score-circle');
        if (scoreCircle) {
          scoreCircle.style.borderColor = isCorrect ? '#10b981' : '#ef4444';
          scoreCircle.style.color = isCorrect ? '#10b981' : '#ef4444';
        }
        if (feedbackSummaryTitle) {
          feedbackSummaryTitle.textContent = isCorrect ? '✓ Correct Choice!' : `✗ Incorrect (Correct: Option ${currentQ.correct})`;
        }
        if (feedbackMainText) {
          feedbackMainText.textContent = feedback;
        }
        if (mcqExplanationText) {
          mcqExplanationText.textContent = explanation;
        }

        // Configure next button
        if (nextBtn) {
          if (currentIndex < totalCount - 1) {
            nextBtn.textContent = 'Next Question →';
          } else {
            nextBtn.textContent = 'Complete Drill & View Scorecard 🏆';
          }
        }

        // Show feedback immediately (0ms)
        if (feedbackSection) {
          feedbackSection.style.display = 'block';
          feedbackSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }

        // Non-blocking background sync with server
        fetch('/interview/assess', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            interview_type: 'mcq',
            selected_option: selectedOptionId,
            correct_option: currentQ.correct,
            explanation: currentQ.explanation
          }),
        }).catch((err) => console.debug('MCQ background sync notice:', err));

      } else {
        // STAR Mode (Instant 0ms Local Rubric Evaluation)
        const answer = answerTextarea.value.trim();
        if (!answer) {
          showInterviewModal({
            title: 'Answer Required',
            message: 'Please write or record an answer before requesting AI feedback.',
            icon: '✍️',
            onConfirm: () => {
              if (answerTextarea) answerTextarea.focus();
            }
          });
          return;
        }

        // Zero-Latency high-precision local evaluation
        const localResult = evaluateStarLocally(answer);
        isAssessed = true;
        assessBtn.disabled = true;
        assessBtn.textContent = 'Answer Evaluated ✓';

        scores.push(localResult.score);
        sessionResults.push({
          question: qText,
          category: qCat,
          score: localResult.score,
          answer: answer,
          feedback: localResult.feedback,
        });

        // Update current pill with score immediately
        const pill = document.getElementById(`q-pill-${currentIndex}`);
        const pillScore = document.getElementById(`q-pill-score-${currentIndex}`);
        if (pill) {
          pill.classList.remove('q-pill-active', 'q-pill-pending');
          pill.classList.add('q-pill-done');
        }
        if (pillScore) {
          pillScore.textContent = `${localResult.score}%`;
        }

        // Calculate and update running score immediately
        const runningAvg = Math.round(scores.reduce((a, b) => a + b, 0) / scores.length);
        if (runningScoreValue) runningScoreValue.textContent = runningAvg;

        // Populate feedback card
        if (questionScoreNum) questionScoreNum.textContent = localResult.score;
        const scoreCircle = document.getElementById('question-score-circle');
        if (scoreCircle) {
          if (localResult.score >= 80) {
            scoreCircle.style.borderColor = '#059669';
            scoreCircle.style.color = '#059669';
          } else if (localResult.score >= 65) {
            scoreCircle.style.borderColor = 'var(--accent, #6d5dfc)';
            scoreCircle.style.color = 'var(--accent, #6d5dfc)';
          } else if (localResult.score >= 45) {
            scoreCircle.style.borderColor = '#f59e0b';
            scoreCircle.style.color = '#f59e0b';
          } else {
            scoreCircle.style.borderColor = '#ef4444';
            scoreCircle.style.color = '#ef4444';
          }
        }
        if (feedbackSummaryTitle) {
          if (localResult.score >= 80) feedbackSummaryTitle.textContent = '🌟 Strong Response';
          else if (localResult.score >= 65) feedbackSummaryTitle.textContent = '👍 Good Answer';
          else if (localResult.score >= 45) feedbackSummaryTitle.textContent = '💡 Good Start · Needs More Depth';
          else feedbackSummaryTitle.textContent = '⚠️ Needs More Structure';
        }
        if (feedbackMainText) feedbackMainText.textContent = localResult.feedback;

        // STAR Badges
        if (localResult.star) {
          Object.keys(starBadges).forEach((key) => {
            const badge = starBadges[key];
            if (badge) {
              const fullKey = key === 's' ? 'situation' : key === 't' ? 'task' : key === 'a' ? 'action' : 'result';
              if (localResult.star[fullKey]) {
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
          const strengths = (localResult.strengths && localResult.strengths.length > 0)
            ? localResult.strengths
            : ['Describe a specific project or technical action to unlock tailored strengths.'];
          strengthsList.innerHTML = strengths.map((s) => `<li>${s}</li>`).join('');
        }
        if (improvementsList) {
          improvementsList.innerHTML = (localResult.improvements || []).map((i) => `<li>${i}</li>`).join('');
        }

        // Configure next button
        if (nextBtn) {
          if (currentIndex < totalCount - 1) {
            nextBtn.textContent = 'Next Question →';
          } else {
            nextBtn.textContent = 'Complete Interview & View Scorecard 🏆';
          }
        }

        // Show feedback immediately (0ms)
        if (feedbackSection) {
          feedbackSection.style.display = 'block';
          feedbackSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }

        // Non-blocking background sync with server
        fetch('/interview/assess', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ answer, question: qText, interview_type: 'star' }),
        }).then(async (res) => {
          if (res.ok) {
            const serverResult = await res.json();
            if (serverResult.strengths && serverResult.strengths.length && strengthsList) {
              strengthsList.innerHTML = serverResult.strengths.map((s) => `<li>${s}</li>`).join('');
            }
            if (serverResult.improvements && serverResult.improvements.length && improvementsList) {
              improvementsList.innerHTML = serverResult.improvements.map((i) => `<li>${i}</li>`).join('');
            }
          }
        }).catch((err) => console.debug('STAR background sync notice:', err));
      }
    });
  }

  // Next Question / Finish handler
  if (nextBtn) {
    nextBtn.addEventListener('click', () => {
      stopAllAudio();
      if (currentIndex < totalCount - 1) {
        currentIndex++;
        loadQuestion(currentIndex);
        window.scrollTo({ top: 0, behavior: 'smooth' });
      } else {
        finishInterview();
      }
    });
  }

  // Final summary completion handler (Zero-Latency: 0ms immediate render + non-blocking background record)
  function finishInterview() {
    stopAllAudio();
    const overallAvg = scores.length ? Math.round(scores.reduce((a, b) => a + b, 0) / scores.length) : 0;

    // Asynchronously log session completion without blocking the UI
    fetch('/interview/complete', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ overall_score: overallAvg, question_count: totalCount }),
    }).catch((e) => console.debug('Interview completion sync notice:', e));

    // Populate scorecard
    const finalScoreNum = document.getElementById('final-score-num');
    const finalRatingLabel = document.getElementById('final-rating-label');
    const tableBody = document.getElementById('progression-table-body');

    if (finalScoreNum) finalScoreNum.textContent = overallAvg;
    if (finalRatingLabel) {
      if (isMcq) {
        const correctCount = scores.filter((s) => s === 100).length;
        if (overallAvg >= 80) finalRatingLabel.textContent = `Mastery Demonstrated! 🔥 (${correctCount} of ${totalCount} Correct)`;
        else if (overallAvg >= 60) finalRatingLabel.textContent = `Solid Technical Base 👍 (${correctCount} of ${totalCount} Correct)`;
        else finalRatingLabel.textContent = `Needs Review 📚 (${correctCount} of ${totalCount} Correct)`;
      } else {
        if (overallAvg >= 82) finalRatingLabel.textContent = 'Ready for Real Interviews! 🔥';
        else if (overallAvg >= 68) finalRatingLabel.textContent = 'Solid Performance — Polish metrics to stand out';
        else finalRatingLabel.textContent = 'Good Practice Run — Emphasize the STAR format';
      }
    }

    if (tableBody) {
      if (isMcq) {
        tableBody.innerHTML = sessionResults
          .map(
            (r, idx) => `
          <tr style="border-bottom: 1px solid var(--line);">
            <td style="padding: 12px 10px;">
              <strong>Q${idx + 1}:</strong> ${r.question.slice(0, 75)}...
              <div style="font-size: 0.8rem; color: var(--muted); margin-top: 3px;">
                Your choice: <strong>Option ${r.selected_option}</strong> · Correct answer: <strong>Option ${r.correct_option}</strong>
              </div>
            </td>
            <td style="padding: 12px 10px;">
              <span class="badge" style="background:rgba(109, 93, 252, 0.1); color:var(--accent);">${r.category}</span>
            </td>
            <td style="padding: 12px 10px; text-align: right; font-weight: 800; color: ${
              r.is_correct ? '#087f5b' : '#ef4444'
            };">
              ${r.is_correct ? '✓ 100%' : '✗ 0%'}
            </td>
          </tr>
        `
          )
          .join('');
      } else {
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
            <td style="padding: 12px 10px; text-align: right; font-weight: 800; color: ${
              r.score >= 75 ? '#087f5b' : r.score >= 60 ? 'var(--accent)' : '#f76707'
            };">
              ${r.score}%
            </td>
          </tr>
        `
          )
          .join('');
      }
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
