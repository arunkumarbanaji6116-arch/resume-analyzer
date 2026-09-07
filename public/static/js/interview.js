document.addEventListener('DOMContentLoaded', () => {
  const app = document.getElementById('interview-app');
  if (!app) return;

  const role = app.dataset.role || 'General';
  const selectedVoice = app.dataset.voice || 'rachel';
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

      // Pitch & rate tailored to persona
      if (selectedVoice === 'george') {
        utterance.pitch = 0.82;
        utterance.rate = 0.92;
      } else if (selectedVoice === 'adam') {
        utterance.pitch = 0.90;
        utterance.rate = 0.96;
      } else if (selectedVoice === 'sarah') {
        utterance.pitch = 1.08;
        utterance.rate = 1.0;
      } else {
        // rachel
        utterance.pitch = 1.02;
        utterance.rate = 0.98;
      }

      const voices = window.speechSynthesis.getVoices();
      if (voices && voices.length > 0) {
        const isMale = selectedVoice === 'adam' || selectedVoice === 'george';
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
                name.includes('mark')
              );
            }
            return (
              name.includes('female') ||
              name.includes('zira') ||
              name.includes('samantha') ||
              name.includes('victoria') ||
              name.includes('rachel') ||
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

  // Speaks question text via ElevenLabs API (or fallback synthesis)
  async function speakQuestion(text) {
    if (!text || isMuted) return;
    stopAllAudio();
    setSpeakingUI(true, '🎙️ AI Interviewer Asking Question...');

    try {
      const res = await fetch('/interview/speak', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, voice: selectedVoice }),
      });

      const contentType = res.headers.get('content-type') || '';
      if (res.ok && contentType.includes('audio/mpeg')) {
        const blob = await res.blob();
        currentAudioUrl = URL.createObjectURL(blob);
        const audio = new Audio(currentAudioUrl);
        currentAudio = audio;

        audio.onended = () => {
          stopAllAudio();
          setSpeakingUI(false, '🎧 Listening for your response');
        };

        audio.onerror = (e) => {
          console.warn('Audio element error, falling back to speech synthesis:', e);
          fallbackBrowserSpeech(text, () => {
            setSpeakingUI(false, '🎧 Listening for your response');
          });
        };

        await audio.play();
        return;
      }

      // Backend signaled fallback or key not configured
      fallbackBrowserSpeech(text, () => {
        setSpeakingUI(false, '🎧 Listening for your response');
      });
    } catch (err) {
      console.warn('Voice API request failed, using speech synthesis fallback:', err);
      fallbackBrowserSpeech(text, () => {
        setSpeakingUI(false, '🎧 Listening for your response');
      });
    }
  }

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
    stopAllAudio();

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

  // Submit and Assess Answer
  if (assessBtn) {
    assessBtn.addEventListener('click', async () => {
      stopAllAudio();

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

  // Final summary completion handler
  async function finishInterview() {
    stopAllAudio();
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
