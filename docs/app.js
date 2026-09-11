const STORAGE_KEY = "pomo-pet.web.v1";
const memoryStore = new Map();
const storage = {
  getItem(key) {
    try {
      return memoryStore.get(key) ?? window.localStorage?.getItem(key) ?? null;
    } catch {
      return memoryStore.get(key) ?? null;
    }
  },
  isPersistent() {
    try {
      const key = "__pomo_pet_storage_check";
      window.localStorage?.setItem(key, "1");
      window.localStorage?.removeItem(key);
      return Boolean(window.localStorage);
    } catch {
      return false;
    }
  },
  setItem(key, value) {
    memoryStore.set(key, value);
    try {
      if (!window.localStorage) return false;
      window.localStorage.setItem(key, value);
      memoryStore.delete(key);
      return true;
    } catch {
      // Keep unsaved data available for export even when quota is exhausted.
      return false;
    }
  },
};

const PRESETS = {
  classic: { label: "Classic", work: 25, break: 5, longBreak: 15, interval: 4 },
  sprint: { label: "Sprint", work: 15, break: 3, longBreak: 10, interval: 4 },
  "52-17": { label: "52/17", work: 52, break: 17, longBreak: 17, interval: 0 },
  deep: { label: "Deep", work: 90, break: 20, longBreak: 20, interval: 0 },
};

const DEFAULT_PET_META = {
  frameWidth: 192,
  frameHeight: 208,
  sheetWidth: 1536,
  animations: {
    idle: { row: 0, frames: 6, fps: 8 },
    waving: { row: 3, frames: 4, fps: 8 },
    waiting: { row: 6, frames: 6, fps: 6 },
    running: { row: 7, frames: 6, fps: 10 },
  },
};

const PETS = {
  avocado: {
    label: "Avocado",
    description: "The original calm focus buddy.",
    sprite: "./assets/pets/avacado/spritesheet.webp",
    filter: "none",
    meta: DEFAULT_PET_META,
  },
  mint: {
    label: "Mint",
    description: "Cool, crisp, and steady.",
    sprite: "./assets/pets/avacado/spritesheet.webp",
    filter: "hue-rotate(58deg) saturate(1.2)",
    meta: DEFAULT_PET_META,
  },
  blueberry: {
    label: "Blueberry",
    description: "A calm companion for deep work.",
    sprite: "./assets/pets/avacado/spritesheet.webp",
    filter: "hue-rotate(168deg) saturate(1.18)",
    meta: DEFAULT_PET_META,
  },
  sunrise: {
    label: "Sunrise",
    description: "Warm energy for starting strong.",
    sprite: "./assets/pets/avacado/spritesheet.webp",
    filter: "hue-rotate(318deg) saturate(1.25) brightness(1.08)",
    meta: DEFAULT_PET_META,
  },
};

const INTENTION_PRESETS = ["Deep work", "Study", "Writing", "Coding"];
const ROUTES = ["focus", "tasks", "pets", "stats", "settings"];

const BREAK_PROMPTS = [
  "Look 20 feet away for 20 seconds.",
  "Stand up and roll your shoulders.",
  "Refill water and take five slow breaths.",
  "Walk away from the screen for one minute.",
  "Stretch your wrists and relax your jaw.",
  "Open a window or step into brighter light.",
];

const ACHIEVEMENTS = [
  { id: "first-focus", label: "First Focus", detail: "Complete 1 session.", test: ({ totalSessions }) => totalSessions >= 1 },
  { id: "hour-one", label: "First Hour", detail: "Log 60 focus minutes.", test: ({ totalFocus }) => totalFocus >= 60 },
  { id: "daily-goal", label: "Goal Day", detail: "Reach today's focus goal.", test: ({ goalPercent }) => goalPercent >= 100 },
  { id: "level-two", label: "Level 2 Bond", detail: "Earn 100 XP with your pet.", test: ({ level }) => level >= 2 },
];

const MESSAGES = {
  work: [
    "One clear task. One calm session.",
    "Stay with it. Your pet is focusing too.",
    "Small minutes become big work.",
    "Keep the next step simple.",
  ],
  break: [
    "Look away from the screen for a bit.",
    "Stretch, breathe, reset.",
    "Good work. Let your brain cool down.",
  ],
  long_break: [
    "Long break earned. Step away properly.",
    "Refill, move around, come back fresh.",
  ],
};

const state = loadState();
let ticker = 0;
let hasControl = !("locks" in navigator);
let releaseControl = null;
let controlRequest = null;
let petRequestVersion = 0;
let activeDialog = null;
let dialogReturnFocus = null;
let renderedDay = todayKey();
let audioContext = null;
let wakeLock = null;
let wakeLockRequest = null;
let reviewSessionId = null;
let reviewEnergy = 0;
let customPetResolveTimer = 0;

const els = {
  timerPanel: document.querySelector(".timer-panel"),
  petSprite: document.querySelector("#petSprite"),
  petGallery: document.querySelector("#petGallery"),
  customPetInput: document.querySelector("#customPetInput"),
  customPetStatus: document.querySelector("#customPetStatus"),
  timerText: document.querySelector("#timerText"),
  phaseLabel: document.querySelector("#phaseLabel"),
  sessionLabel: document.querySelector("#sessionLabel"),
  progressFill: document.querySelector("#progressFill"),
  petMessage: document.querySelector("#petMessage"),
  intentionInput: document.querySelector("#intentionInput"),
  activeTaskStatus: document.querySelector("#activeTaskStatus"),
  completeActiveTaskButton: document.querySelector("#completeActiveTaskButton"),
  intentionChips: document.querySelector("#intentionChips"),
  startPauseButton: document.querySelector("#startPauseButton"),
  resetButton: document.querySelector("#resetButton"),
  skipButton: document.querySelector("#skipButton"),
  taskForm: document.querySelector("#taskForm"),
  taskInput: document.querySelector("#taskInput"),
  taskList: document.querySelector("#taskList"),
  taskSummary: document.querySelector("#taskSummary"),
  presetButtons: document.querySelector("#presetButtons"),
  presetSummary: document.querySelector("#presetSummary"),
  workInput: document.querySelector("#workInput"),
  breakInput: document.querySelector("#breakInput"),
  longBreakInput: document.querySelector("#longBreakInput"),
  intervalInput: document.querySelector("#intervalInput"),
  todayDate: document.querySelector("#todayDate"),
  todaySessions: document.querySelector("#todaySessions"),
  todayFocus: document.querySelector("#todayFocus"),
  streakCount: document.querySelector("#streakCount"),
  totalFocus: document.querySelector("#totalFocus"),
  petMood: document.querySelector("#petMood"),
  petLevel: document.querySelector("#petLevel"),
  petXp: document.querySelector("#petXp"),
  goalPercent: document.querySelector("#goalPercent"),
  dailyGoalInput: document.querySelector("#dailyGoalInput"),
  breakPromptSection: document.querySelector("#breakPromptSection"),
  breakPrompt: document.querySelector("#breakPrompt"),
  nextBreakPromptButton: document.querySelector("#nextBreakPromptButton"),
  weekSummary: document.querySelector("#weekSummary"),
  weekChart: document.querySelector("#weekChart"),
  insightSummary: document.querySelector("#insightSummary"),
  insightBestDay: document.querySelector("#insightBestDay"),
  insightEnergy: document.querySelector("#insightEnergy"),
  insightMomentum: document.querySelector("#insightMomentum"),
  achievementSummary: document.querySelector("#achievementSummary"),
  achievementList: document.querySelector("#achievementList"),
  notificationToggle: document.querySelector("#notificationToggle"),
  tickToggle: document.querySelector("#tickToggle"),
  wakeLockToggle: document.querySelector("#wakeLockToggle"),
  offlineStatus: document.querySelector("#offlineStatus"),
  historyList: document.querySelector("#historyList"),
  clearStatsButton: document.querySelector("#clearStatsButton"),
  exportStatsButton: document.querySelector("#exportStatsButton"),
  importStatsButton: document.querySelector("#importStatsButton"),
  importStatsInput: document.querySelector("#importStatsInput"),
  shareSummaryButton: document.querySelector("#shareSummaryButton"),
  dataStatus: document.querySelector("#dataStatus"),
  onboardingOverlay: document.querySelector("#onboardingOverlay"),
  onboardingIntentionInput: document.querySelector("#onboardingIntentionInput"),
  onboardingPresetButtons: document.querySelector("#onboardingPresetButtons"),
  onboardingStartButton: document.querySelector("#onboardingStartButton"),
  sessionReviewOverlay: document.querySelector("#sessionReviewOverlay"),
  sessionReviewInput: document.querySelector("#sessionReviewInput"),
  reviewRating: document.querySelector(".review-rating"),
  saveReviewButton: document.querySelector("#saveReviewButton"),
  skipReviewButton: document.querySelector("#skipReviewButton"),
  routeViews: document.querySelectorAll("[data-route]"),
  routeLinks: document.querySelectorAll("[data-route-link]"),
};

function defaultState() {
  const preset = PRESETS.classic;
  return {
    settings: {
      preset: "classic",
      work: preset.work,
      break: preset.break,
      longBreak: preset.longBreak,
      interval: preset.interval,
      notifications: false,
      tick: false,
      wakeLock: false,
      pet: "avocado",
      customPetUrl: "",
      customPetSourceUrl: "",
      customPetLabel: "",
      customPetMeta: null,
      dailyGoalMinutes: 120,
      currentIntention: "",
      activeTaskId: "",
      breakPromptIndex: 0,
      onboarded: false,
    },
    timer: {
      phase: "work",
      remaining: preset.work * 60,
      running: false,
      deadline: null,
      duration: preset.work * 60,
      started: false,
      context: null,
      sessionsCompleted: 0,
      message: MESSAGES.work[0],
    },
    stats: {
      sessions: [],
      tasks: [],
      bestStreak: 0,
    },
  };
}

function loadState() {
  try {
    const saved = JSON.parse(storage.getItem(STORAGE_KEY));
    return saved ? mergeState(defaultState(), saved) : defaultState();
  } catch {
    return defaultState();
  }
}

function bounded(value, fallback, min, max) {
  return typeof value === "number" && Number.isFinite(value)
    ? Math.max(min, Math.min(max, Math.round(value))) : fallback;
}

function mergeState(base, saved) {
  if (!saved || typeof saved !== "object") return base;
  const settings = { ...base.settings, ...sanitizeImportedSettings(saved.settings || {}) };
  const raw = saved.timer || {};
  const phase = ["work", "break", "long_break"].includes(raw.phase) ? raw.phase : "work";
  const configuredDuration = (phase === "work" ? settings.work : phase === "break" ? settings.break : settings.longBreak) * 60;
  const duration = bounded(raw.duration, configuredDuration, 60, 10800);
  const remaining = typeof raw.remaining === "number" && raw.remaining > 0
    ? bounded(raw.remaining, duration, 0, duration) : duration;
  const context = raw.context && typeof raw.context === "object" ? {
    intention: String(raw.context.intention || "").slice(0, 80),
    taskId: String(raw.context.taskId || ""),
    preset: String(raw.context.preset || "custom").slice(0, 40),
  } : null;
  return {
    settings,
    timer: {
      phase, duration, remaining, context,
      started: raw.started === true || remaining < duration,
      running: raw.running === true && Number.isFinite(raw.deadline) && raw.deadline > 0,
      deadline: Number.isFinite(raw.deadline) ? raw.deadline : null,
      sessionsCompleted: bounded(raw.sessionsCompleted, 0, 0, 1000000),
      message: typeof raw.message === "string" ? raw.message.slice(0, 220) : MESSAGES[phase][0],
    },
    stats: normalizeImportedStats(saved.stats || {}),
  };
}

function saveState() {
  const persisted = storage.setItem(STORAGE_KEY, JSON.stringify(state));
  if (!persisted) {
    const notice = document.querySelector("#storageNotice");
    notice.hidden = false;
    notice.textContent = "Your latest changes could not be saved. Export your work before closing this tab.";
  }
}

function durationForPhase(phase = state.timer.phase) {
  if (phase === "work") return state.settings.work * 60;
  if (phase === "long_break") return state.settings.longBreak * 60;
  return state.settings.break * 60;
}

function phaseName(phase = state.timer.phase) {
  if (phase === "long_break") return "Long break";
  return phase[0].toUpperCase() + phase.slice(1);
}

function formatTime(seconds) {
  const minutes = Math.floor(seconds / 60).toString().padStart(2, "0");
  const secs = Math.floor(seconds % 60).toString().padStart(2, "0");
  return `${minutes}:${secs}`;
}

function todayKey(date = new Date()) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
}

function sessionsToday() {
  const today = todayKey();
  return state.stats.sessions.filter((session) => session.date === today);
}

function computeStreak() {
  const days = [...new Set(state.stats.sessions.map((session) => session.date))].sort().reverse();
  if (!days.length) return 0;

  let streak = 0;
  const cursor = new Date();
  if (days[0] !== todayKey(cursor)) cursor.setDate(cursor.getDate() - 1);
  for (const day of days) {
    if (day !== todayKey(cursor)) break;
    streak += 1;
    cursor.setDate(cursor.getDate() - 1);
  }
  state.stats.bestStreak = Math.max(state.stats.bestStreak, streak);
  return streak;
}

function pickMessage(phase) {
  const choices = MESSAGES[phase] || MESSAGES.work;
  return choices[Math.floor(Math.random() * choices.length)];
}

function normalizeBreakPromptIndex(value) {
  const index = Number(value);
  if (!Number.isFinite(index)) return 0;
  return Math.max(0, Math.floor(index)) % BREAK_PROMPTS.length;
}

function currentBreakPrompt() {
  return BREAK_PROMPTS[normalizeBreakPromptIndex(state.settings.breakPromptIndex)];
}

function nextBreakPrompt() {
  state.settings.breakPromptIndex = (normalizeBreakPromptIndex(state.settings.breakPromptIndex) + 1) % BREAK_PROMPTS.length;
  saveState();
  render();
}

function renderPresetButtons() {
  els.presetButtons.innerHTML = "";
  Object.entries(PRESETS).forEach(([id, preset]) => {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = preset.label;
    button.setAttribute("aria-pressed", String(state.settings.preset === id));
    button.addEventListener("click", () => applyPreset(id));
    els.presetButtons.append(button);
  });
}

function renderOnboardingPresets() {
  els.onboardingPresetButtons.innerHTML = "";
  Object.entries(PRESETS).forEach(([id, preset]) => {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = preset.label;
    button.setAttribute("aria-pressed", String(state.settings.preset === id));
    button.addEventListener("click", () => {
      state.settings = {
        ...state.settings,
        preset: id,
        work: preset.work,
        break: preset.break,
        longBreak: preset.longBreak,
        interval: preset.interval,
      };
      state.timer.phase = "work";
      state.timer.duration = durationForPhase("work");
      state.timer.remaining = state.timer.duration;
      saveState();
      render();
    });
    els.onboardingPresetButtons.append(button);
  });
}

function renderPetGallery() {
  els.petGallery.innerHTML = "";
  Object.entries(PETS).forEach(([id, pet]) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "pet-choice";
    button.setAttribute("aria-pressed", String(state.settings.pet === id && !state.settings.customPetUrl));
    button.innerHTML = `
      <span class="pet-choice-preview" style="background-image: url('${pet.sprite}'); filter: ${pet.filter}"></span>
      <span>
        <strong>${pet.label}</strong>
        <small>${pet.description}</small>
      </span>
    `;
    button.addEventListener("click", () => {
      petRequestVersion += 1;
      window.clearTimeout(customPetResolveTimer);
      state.settings.pet = id;
      state.settings.customPetUrl = "";
      state.settings.customPetSourceUrl = "";
      state.settings.customPetLabel = "";
      state.settings.customPetMeta = null;
      saveState();
      render();
    });
    els.petGallery.append(button);
  });
}

function currentPet() {
  return PETS[state.settings.pet] || PETS.avocado;
}

function petVisualFilter(filterValue) {
  const colorFilter = filterValue && filterValue !== "none" ? filterValue : "";
  return [colorFilter, "drop-shadow(0 20px 34px rgba(0, 0, 0, 0.24))"].filter(Boolean).join(" ");
}

function renderIntentionChips() {
  els.intentionChips.innerHTML = "";
  INTENTION_PRESETS.forEach((label) => {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = label;
    button.setAttribute("aria-pressed", String(state.settings.currentIntention === label));
    button.addEventListener("click", () => {
      state.settings.activeTaskId = "";
      state.settings.currentIntention = label;
      saveState();
      render();
    });
    els.intentionChips.append(button);
  });
}

function renderTasks() {
  const tasks = normalizeTasks(state.stats.tasks);
  if (tasks.length !== state.stats.tasks.length) {
    state.stats.tasks = tasks;
    saveState();
  }
  const openTasks = tasks.filter((task) => !task.completed);
  els.taskSummary.textContent = `${openTasks.length} open`;
  els.taskList.innerHTML = "";

  if (!tasks.length) {
    const empty = document.createElement("p");
    empty.className = "task-empty";
    empty.textContent = "Add one task to make the next session obvious.";
    els.taskList.append(empty);
    return;
  }

  tasks.forEach((task) => {
    const item = document.createElement("article");
    item.className = "task-item";
    item.dataset.completed = String(task.completed);
    item.dataset.active = String(task.id === state.settings.activeTaskId);
    item.innerHTML = `
      <label class="task-check">
        <input type="checkbox" ${task.completed ? "checked" : ""} aria-label="Complete ${escapeAttribute(task.title)}">
        <span>${task.completed ? "Done" : "Open"}</span>
      </label>
      <button class="task-select" type="button">
        <strong>${escapeHtml(task.title)}</strong>
        <small>${task.focusMinutes ? `${task.focusMinutes}m focused` : "Ready for focus"}</small>
      </button>
      <button class="task-delete" type="button" aria-label="Delete ${escapeAttribute(task.title)}">Remove</button>
    `;
    item.querySelector(".task-check input").addEventListener("change", (event) => toggleTask(task.id, event.target.checked));
    item.querySelector(".task-select").addEventListener("click", () => selectTask(task.id));
    item.querySelector(".task-delete").addEventListener("click", () => deleteTask(task.id));
    els.taskList.append(item);
  });
}

function addTask(title) {
  const cleanedTitle = title.trim().replace(/\s+/g, " ").slice(0, 80);
  if (!cleanedTitle) return;
  const task = {
    id: crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}`,
    title: cleanedTitle,
    completed: false,
    focusMinutes: 0,
    createdAt: new Date().toISOString(),
    completedAt: "",
  };
  state.stats.tasks = [task, ...normalizeTasks(state.stats.tasks)];
  selectTask(task.id, { persist: false });
  els.taskInput.value = "";
  saveState();
  render();
}

function selectTask(taskId, { persist = true } = {}) {
  const task = state.stats.tasks.find((item) => item.id === taskId);
  if (!task || task.completed) return;
  state.settings.activeTaskId = task.id;
  state.settings.currentIntention = task.title;
  if (persist) {
    saveState();
    render();
  }
}

function toggleTask(taskId, completed) {
  const task = state.stats.tasks.find((item) => item.id === taskId);
  if (!task) return;
  task.completed = Boolean(completed);
  task.completedAt = task.completed ? new Date().toISOString() : "";
  if (task.completed && state.settings.activeTaskId === task.id) {
    state.settings.activeTaskId = "";
  } else if (!task.completed) {
    state.settings.activeTaskId = task.id;
    state.settings.currentIntention = task.title;
  }
  saveState();
  render();
}

function activeTask() {
  return state.stats.tasks.find((task) => task.id === state.settings.activeTaskId && !task.completed) || null;
}

function completeActiveTask() {
  const task = activeTask();
  if (!task) return;
  toggleTask(task.id, true);
}

function deleteTask(taskId) {
  if (!window.confirm("Remove this task? Its completed sessions will stay in history.")) return;
  state.stats.tasks = state.stats.tasks.filter((task) => task.id !== taskId);
  if (state.settings.activeTaskId === taskId) {
    state.settings.activeTaskId = "";
  }
  saveState();
  render();
}

function setInputValue(input, value) {
  if (document.activeElement !== input) input.value = value;
}

function renderClock() {
  const progress = Math.max(0, Math.min(1, state.timer.remaining / state.timer.duration));
  els.timerText.textContent = formatTime(state.timer.remaining);
  els.progressFill.style.width = `${(1 - progress) * 100}%`;
  els.timerPanel.style.setProperty("--session-progress", `${(1 - progress) * 100}%`);
  const shortcut = document.querySelector("#timerShortcut");
  shortcut.textContent = `${formatTime(state.timer.remaining)} · ${phaseName()}${state.timer.started && !state.timer.running ? " paused" : ""}`;
  shortcut.hidden = currentRoute() === "focus";
  document.querySelector("#timerHint").textContent = state.timer.running
    ? "Keep going. Your timer continues in the background."
    : state.timer.started ? "Paused. Pick up where you left off." : "Ready when you are.";
  updateDocumentTitle();
}

function render() {
  const total = Math.max(state.timer.duration, 1);
  const progress = Math.max(0, Math.min(1, state.timer.remaining / total));
  const elapsedProgress = 1 - progress;
  const todaySessions = sessionsToday();
  const todayFocus = todaySessions.reduce((sum, session) => sum + session.focusMinutes, 0);
  const allFocus = state.stats.sessions.reduce((sum, session) => sum + session.focusMinutes, 0);
  const bond = computeBond(allFocus, todayFocus);
  const streak = computeStreak();
  const pet = currentPet();
  const customSprite = isRenderableSpriteUrl(state.settings.customPetUrl) ? state.settings.customPetUrl : "";
  const sprite = customSprite || pet.sprite;
  const petMeta = customSprite ? state.settings.customPetMeta || DEFAULT_PET_META : pet.meta || DEFAULT_PET_META;

  els.timerText.textContent = formatTime(state.timer.remaining);
  els.timerPanel.dataset.phase = state.timer.phase;
  els.timerPanel.dataset.running = String(state.timer.running);
  els.timerPanel.style.setProperty("--session-progress", `${elapsedProgress * 100}%`);
  els.phaseLabel.textContent = phaseName();
  els.sessionLabel.textContent = `${state.timer.sessionsCompleted} sessions`;
  els.progressFill.style.width = `${elapsedProgress * 100}%`;
  els.petMessage.textContent = state.timer.message;
  setInputValue(els.intentionInput, state.settings.currentIntention);
  const currentTask = activeTask();
  els.activeTaskStatus.textContent = currentTask ? `Task: ${currentTask.title}` : "No task selected";
  els.completeActiveTaskButton.disabled = !currentTask;
  els.startPauseButton.textContent = state.timer.running ? "Pause" : state.timer.started ? "Resume" : "Start";
  els.presetSummary.textContent = `${state.settings.work} / ${state.settings.break}`;
  setInputValue(els.workInput, state.settings.work);
  setInputValue(els.breakInput, state.settings.break);
  setInputValue(els.longBreakInput, state.settings.longBreak);
  setInputValue(els.intervalInput, state.settings.interval);
  els.todayDate.textContent = new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric" }).format(new Date());
  els.todaySessions.textContent = todaySessions.length;
  els.todayFocus.textContent = `${todayFocus}m`;
  els.streakCount.textContent = streak;
  els.totalFocus.textContent = formatFocusHours(allFocus);
  els.petMood.textContent = bond.mood;
  els.petLevel.textContent = `Level ${bond.level}`;
  els.petXp.textContent = `${allFocus} XP`;
  els.goalPercent.textContent = `${bond.goalPercent}%`;
  els.goalPercent.parentElement.style.setProperty("--goal-progress", `${bond.goalPercent}%`);
  setInputValue(els.dailyGoalInput, state.settings.dailyGoalMinutes);
  els.breakPrompt.textContent = currentBreakPrompt();
  els.breakPromptSection.dataset.active = String(state.timer.phase !== "work");
  els.notificationToggle.checked = state.settings.notifications;
  els.tickToggle.checked = state.settings.tick;
  els.wakeLockToggle.checked = state.settings.wakeLock;
  setInputValue(els.customPetInput, state.settings.customPetSourceUrl || state.settings.customPetUrl);
  els.customPetStatus.textContent = customPetStatusText(customSprite);
  els.offlineStatus.textContent = storage.isPersistent() ? "local" : "session";
  updateDocumentTitle();
  syncWakeLock();

  els.petSprite.className = "pet-sprite";
  els.petSprite.style.filter = petVisualFilter(customSprite ? "" : pet.filter);
  els.petSprite.setAttribute("aria-label", `Animated ${customSprite ? "custom" : pet.label.toLowerCase()} pet`);
  applyPetSprite(petMeta, sprite);
  if (!state.timer.running) els.petSprite.classList.add("is-paused");
  else if (state.timer.phase === "work") els.petSprite.classList.add("is-running");
  else els.petSprite.classList.add("is-break");

  renderPresetButtons();
  renderOnboardingPresets();
  renderPetGallery();
  renderIntentionChips();
  renderTasks();
  renderHistory();
  renderWeekChart();
  renderInsights();
  renderAchievements({ allFocus, todayFocus, bond });
  renderOnboarding();
  renderSessionReview();
  renderRoute();
  renderClock();
  syncDialog();
  if (!hasControl) document.querySelectorAll("button, input, textarea").forEach((control) => { control.disabled = true; });
}

function currentRoute() {
  const route = window.location.hash.replace(/^#\/?/, "") || "focus";
  return ROUTES.includes(route) ? route : "focus";
}

function rawRoute() {
  return window.location.hash.replace(/^#\/?/, "") || "focus";
}

function renderRoute() {
  const route = currentRoute();
  els.routeViews.forEach((view) => {
    view.hidden = view.dataset.route !== route;
  });
  els.routeLinks.forEach((link) => {
    const active = link.dataset.routeLink === route;
    link.setAttribute("aria-current", active ? "page" : "false");
  });
  document.body.dataset.activeRoute = route;
  renderClock();
}

function syncRoute() {
  if (!ROUTES.includes(rawRoute())) {
    window.location.hash = "#/focus";
    return;
  }
  renderRoute();
  window.scrollTo({ top: 0, left: 0, behavior: "instant" });
}

function applyPetSprite(meta, spriteUrl) {
  const animationName = spriteAnimationName();
  const baseAnimation = meta.animations[animationName] || meta.animations.idle || DEFAULT_PET_META.animations.idle;
  const animation = state.timer.running ? baseAnimation : { ...baseAnimation, row: 0, frames: 1, fps: 1 };
  const frameWidth = meta.frameWidth || DEFAULT_PET_META.frameWidth;
  const frameHeight = meta.frameHeight || DEFAULT_PET_META.frameHeight;
  const frames = Math.max(1, Number(animation.frames) || 1);
  const fps = Math.max(1, Number(animation.fps) || 8);
  const row = Math.max(0, Number(animation.row) || 0);
  const sheetWidth = meta.sheetWidth || frameWidth * maxAnimationFrames(meta);

  els.petSprite.style.backgroundImage = `url("${spriteUrl}")`;
  els.petSprite.style.setProperty("--pet-frame-width", `${frameWidth}px`);
  els.petSprite.style.setProperty("--pet-frame-height", `${frameHeight}px`);
  els.petSprite.style.setProperty("--pet-sheet-width", `${sheetWidth}px`);
  els.petSprite.style.setProperty("--pet-row-offset", `${-(row * frameHeight)}px`);
  els.petSprite.style.setProperty("--pet-end-offset", `${-(frames * frameWidth)}px`);
  els.petSprite.style.setProperty("--pet-frames", frames);
  els.petSprite.style.setProperty("--pet-duration", `${frames / fps}s`);
}

function customPetStatusText(customSprite) {
  if (customSprite && state.settings.customPetSourceUrl) return `Loaded ${state.settings.customPetLabel || "Codex Pets link"}.`;
  if (customSprite) return "Using direct spritesheet.";
  if (state.settings.customPetUrl || state.settings.customPetSourceUrl) return "Paste a direct spritesheet or Codex Pets link.";
  return "";
}

function spriteAnimationName() {
  if (!state.timer.running) return "idle";
  return state.timer.phase === "work" ? "running" : "waving";
}

function maxAnimationFrames(meta) {
  return Math.max(...Object.values(meta.animations || DEFAULT_PET_META.animations).map((animation) => Number(animation.frames) || 1), 1);
}

function renderOnboarding() {
  els.onboardingOverlay.hidden = state.settings.onboarded;
  setInputValue(els.onboardingIntentionInput, state.settings.currentIntention);
}

function renderSessionReview() {
  els.sessionReviewOverlay.hidden = !reviewSessionId;
  els.reviewRating.querySelectorAll("button").forEach((button) => {
    button.setAttribute("aria-pressed", String(Number(button.dataset.energy) === reviewEnergy));
  });
}

function updateDocumentTitle() {
  const phase = phaseName();
  if (state.timer.running) {
    document.title = `${formatTime(state.timer.remaining)} ${phase} - Pomo Pet`;
  } else {
    document.title = `Pomo Pet - ${phase} ready`;
  }
}

function formatFocusHours(minutes) {
  if (minutes < 60) return `${minutes}m`;
  const hours = Math.round((minutes / 60) * 10) / 10;
  return `${hours}h`;
}

function computeBond(totalFocusMinutes, todayFocusMinutes) {
  const level = Math.floor(totalFocusMinutes / 100) + 1;
  const goal = Math.max(state.settings.dailyGoalMinutes, 1);
  const goalPercent = Math.min(100, Math.round((todayFocusMinutes / goal) * 100));
  let mood = "ready";
  if (goalPercent >= 100) mood = "proud";
  else if (goalPercent >= 60) mood = "glowing";
  else if (goalPercent >= 25) mood = "warming up";
  return { level, goalPercent, mood };
}

function renderHistory() {
  const recent = [...state.stats.sessions].slice(-5).reverse();
  els.historyList.innerHTML = "";
  if (!recent.length) {
    const item = document.createElement("li");
    item.textContent = "No completed sessions yet.";
    els.historyList.append(item);
    return;
  }

  recent.forEach((session) => {
    const item = document.createElement("li");
    const intention = session.intention ? ` — ${session.intention}` : "";
    const energy = session.energy ? ` — ${session.energy}/5 energy` : "";
    const reflection = session.reflection ? ` — ${session.reflection}` : "";
    item.textContent = `${session.date} · ${session.focusMinutes}m ${session.preset} session at ${session.time}${intention}${energy}${reflection}`;
    els.historyList.append(item);
  });
}

function renderAchievements({ allFocus, todayFocus, bond }) {
  const context = {
    totalSessions: state.stats.sessions.length,
    totalFocus: allFocus,
    todayFocus,
    goalPercent: bond.goalPercent,
    level: bond.level,
  };
  const unlocked = ACHIEVEMENTS.filter((achievement) => achievement.test(context));

  els.achievementSummary.textContent = `${unlocked.length} / ${ACHIEVEMENTS.length}`;
  els.achievementList.innerHTML = "";
  ACHIEVEMENTS.forEach((achievement) => {
    const unlockedAchievement = achievement.test(context);
    const item = document.createElement("div");
    item.className = "achievement-item";
    item.setAttribute("data-unlocked", String(unlockedAchievement));
    item.innerHTML = `
      <span>${unlockedAchievement ? "Done" : "Locked"}</span>
      <strong>${achievement.label}</strong>
      <small>${achievement.detail}</small>
    `;
    els.achievementList.append(item);
  });
}

function renderWeekChart() {
  const days = lastSevenDays();
  const minutesByDay = new Map(days.map((day) => [day.key, 0]));
  state.stats.sessions.forEach((session) => {
    if (minutesByDay.has(session.date)) {
      minutesByDay.set(session.date, minutesByDay.get(session.date) + session.focusMinutes);
    }
  });

  const values = days.map((day) => minutesByDay.get(day.key));
  const max = Math.max(...values, 1);
  const weekTotal = values.reduce((sum, value) => sum + value, 0);

  els.weekSummary.textContent = `${weekTotal}m`;
  els.weekChart.innerHTML = "";
  days.forEach((day, index) => {
    const value = values[index];
    const item = document.createElement("div");
    item.className = "week-bar";
    item.innerHTML = `
      <span class="week-fill" style="height: ${value ? Math.max(4, (value / max) * 100) : 0}%"></span>
      <strong>${day.label}</strong>
      <small>${value}m</small>
    `;
    els.weekChart.append(item);
  });
}

function renderInsights() {
  const currentDays = lastNDays(7, 0);
  const previousDays = lastNDays(7, 7);
  const currentKeys = new Set(currentDays.map((day) => day.key));
  const previousKeys = new Set(previousDays.map((day) => day.key));
  const minutesByDay = new Map(currentDays.map((day) => [day.key, 0]));
  let currentTotal = 0;
  let previousTotal = 0;

  state.stats.sessions.forEach((session) => {
    if (currentKeys.has(session.date)) {
      currentTotal += session.focusMinutes;
      minutesByDay.set(session.date, minutesByDay.get(session.date) + session.focusMinutes);
    } else if (previousKeys.has(session.date)) {
      previousTotal += session.focusMinutes;
    }
  });

  const bestDay = currentDays.reduce((best, day) => {
    const minutes = minutesByDay.get(day.key);
    return minutes > best.minutes ? { ...day, minutes } : best;
  }, { label: "", key: "", minutes: 0 });
  const averageEnergy = averageSessionEnergy(state.stats.sessions);
  const delta = currentTotal - previousTotal;

  els.insightSummary.textContent = `${currentTotal}m`;
  els.insightBestDay.textContent = bestDay.minutes ? `${bestDay.label} ${bestDay.minutes}m` : "none yet";
  els.insightEnergy.textContent = averageEnergy ? `${averageEnergy}/5` : "unrated";
  els.insightMomentum.textContent = delta === 0
    ? "steady"
    : `${delta > 0 ? "+" : ""}${delta}m`;
}

function lastSevenDays() {
  return lastNDays(7, 0);
}

function lastNDays(count, offsetDays = 0) {
  const formatter = new Intl.DateTimeFormat(undefined, { weekday: "narrow" });
  return Array.from({ length: count }, (_, index) => {
    const date = new Date();
    date.setDate(date.getDate() - offsetDays - (count - 1 - index));
    return {
      key: todayKey(date),
      label: formatter.format(date),
    };
  });
}

function applyPreset(id) {
  if (state.timer.started && !window.confirm("Change preset and reset the current session?")) return;
  const preset = PRESETS[id];
  state.settings = {
    ...state.settings,
    preset: id,
    work: preset.work,
    break: preset.break,
    longBreak: preset.longBreak,
    interval: preset.interval,
  };
  resetTimer();
}

function updateSetting(key, value) {
  state.settings[key] = value;
  if (["work", "break", "longBreak", "interval"].includes(key)) {
    state.settings.preset = "custom";
    if (!state.timer.started) {
      state.timer.duration = durationForPhase();
      state.timer.remaining = state.timer.duration;
    }
  }
  saveState();
  render();
}

function startPause() {
  if (state.timer.running) {
    tick();
    if (!state.timer.running) return;
    state.timer.running = false;
    state.timer.deadline = null;
  } else {
    if (!state.timer.started) {
      state.timer.context = {
        taskId: state.settings.activeTaskId,
        intention: state.settings.currentIntention,
        preset: state.settings.preset,
      };
    }
    state.timer.started = true;
    state.timer.running = true;
    state.timer.deadline = Date.now() + state.timer.remaining * 1000;
    unlockAudio();
  }
  saveState();
  render();
}

function resetTimer({ confirm = false } = {}) {
  if (confirm && state.timer.started && !window.confirm("Reset this session? Unfinished focus time will not be counted.")) return;
  state.timer.running = false;
  state.timer.deadline = null;
  state.timer.started = false;
  state.timer.context = null;
  state.timer.phase = "work";
  state.timer.duration = durationForPhase("work");
  state.timer.remaining = state.timer.duration;
  state.timer.message = pickMessage("work");
  saveState();
  render();
}

function skipPhase() {
  if (state.timer.started && !window.confirm("Skip this phase? Unfinished focus time will not be counted.")) return;
  completePhase({ skipped: true });
}

function completePhase({ skipped = false } = {}) {
  if (state.timer.phase === "work") {
    state.timer.sessionsCompleted += skipped ? 0 : 1;
    if (!skipped) openSessionReview(recordSession());
    const shouldLongBreak = !skipped && state.settings.interval > 0
      && state.timer.sessionsCompleted > 0
      && state.timer.sessionsCompleted % state.settings.interval === 0;
    state.timer.phase = shouldLongBreak ? "long_break" : "break";
    state.settings.breakPromptIndex = (normalizeBreakPromptIndex(state.settings.breakPromptIndex) + 1) % BREAK_PROMPTS.length;
  } else {
    state.timer.phase = "work";
  }

  state.timer.running = false;
  state.timer.deadline = null;
  state.timer.started = false;
  state.timer.context = null;
  state.timer.duration = durationForPhase();
  state.timer.remaining = state.timer.duration;
  state.timer.message = pickMessage(state.timer.phase);
  notifyPhase();
  saveState();
  render();
}

function recordSession() {
  const now = new Date(state.timer.deadline || Date.now());
  const context = state.timer.context || state.settings;
  const session = {
    id: crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}`,
    date: todayKey(now),
    time: new Intl.DateTimeFormat(undefined, { hour: "numeric", minute: "2-digit" }).format(now),
    preset: context.preset,
    pet: isRenderableSpriteUrl(state.settings.customPetUrl) ? "custom" : currentPet().label,
    taskId: context.taskId ?? state.settings.activeTaskId,
    intention: context.intention ?? state.settings.currentIntention,
    reflection: "",
    energy: 0,
    focusMinutes: state.timer.duration / 60,
    completedAt: now.toISOString(),
  };
  state.stats.sessions.push(session);
  creditActiveTask(session.focusMinutes, session.taskId);
  return session.id;
}

function creditActiveTask(focusMinutes, taskId) {
  const task = state.stats.tasks.find((item) => item.id === taskId);
  if (!task) return;
  task.focusMinutes = Math.max(0, Number(task.focusMinutes) || 0) + focusMinutes;
}

function openSessionReview(sessionId) {
  reviewSessionId = sessionId;
  reviewEnergy = 0;
  els.sessionReviewInput.value = "";
}

function saveSessionReview() {
  const session = state.stats.sessions.find((item) => item.id === reviewSessionId);
  if (session) {
    session.reflection = els.sessionReviewInput.value.trim().slice(0, 220);
    session.energy = reviewEnergy;
    saveState();
    setDataStatus(session.reflection ? "Session note saved." : "Session rating saved.");
  }
  closeSessionReview();
}

function closeSessionReview() {
  reviewSessionId = null;
  reviewEnergy = 0;
  els.sessionReviewInput.value = "";
  render();
}

function exportStats() {
  const payload = {
    exportedAt: new Date().toISOString(),
    app: "Pomo Pet Web",
    settings: state.settings,
    stats: state.stats,
  };
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `pomo-pet-stats-${todayKey()}.json`;
  link.click();
  URL.revokeObjectURL(url);
}

async function importStatsFromFile(file) {
  if (!file) return;
  try {
    if (file.size > 10 * 1024 * 1024) throw new Error("File too large");
    const payload = JSON.parse(await file.text());
    if (!payload || typeof payload !== "object" || !Array.isArray((payload.stats || payload).sessions)) throw new Error("Invalid export");
    if ((payload.stats || payload).sessions.some((session) => !normalizeImportedSession(session))) throw new Error("Invalid session");
    const importedStats = normalizeImportedStats(payload.stats || payload);
    const importedSettings = payload.settings && typeof payload.settings === "object" ? payload.settings : {};

    if (!window.confirm(`Replace your local history and tasks with ${importedStats.sessions.length} imported sessions? Export first to keep a backup.`)) return;
    state.stats = importedStats;
    state.settings = { ...state.settings, ...sanitizeImportedSettings(importedSettings) };
    reviewSessionId = null;
    resetTimer();
    saveState();
    setDataStatus(`Imported ${state.stats.sessions.length} sessions.`);
    render();
  } catch {
    setDataStatus("Import failed. Use a Pomo Pet JSON export.");
  } finally {
    els.importStatsInput.value = "";
  }
}

function normalizeImportedStats(stats) {
  stats = stats && typeof stats === "object" ? stats : {};
  const sessions = Array.isArray(stats.sessions)
    ? stats.sessions.map(normalizeImportedSession).filter(Boolean)
    : [];
  return {
    sessions,
    tasks: normalizeTasks(stats.tasks || []),
    bestStreak: Number.isFinite(Number(stats.bestStreak)) ? Number(stats.bestStreak) : 0,
  };
}

function normalizeImportedSession(session) {
  if (!session || typeof session !== "object") return null;
  const focusMinutes = Number(session.focusMinutes);
  if (!Number.isFinite(focusMinutes) || focusMinutes <= 0 || focusMinutes > 180 || !/^\d{4}-\d{2}-\d{2}$/.test(session.date) || Number.isNaN(Date.parse(session.date))) return null;
  return {
    id: String(session.id || `${Date.now()}-${Math.random()}`),
    date: typeof session.date === "string" ? session.date : todayKey(),
    time: typeof session.time === "string" ? session.time : "",
    preset: typeof session.preset === "string" ? session.preset : "custom",
    pet: typeof session.pet === "string" ? session.pet : "Avocado",
    taskId: typeof session.taskId === "string" ? session.taskId : "",
    intention: typeof session.intention === "string" ? session.intention : "",
    reflection: typeof session.reflection === "string" ? session.reflection.slice(0, 220) : "",
    energy: normalizeEnergy(session.energy),
    focusMinutes,
    completedAt: typeof session.completedAt === "string" ? session.completedAt : new Date().toISOString(),
  };
}

function normalizeTasks(tasks) {
  if (!Array.isArray(tasks)) return [];
  return tasks.map(normalizeTask).filter(Boolean);
}

function normalizeTask(task) {
  if (!task || typeof task !== "object") return null;
  const title = typeof task.title === "string" ? task.title.trim().replace(/\s+/g, " ").slice(0, 80) : "";
  if (!title) return null;
  return {
    id: String(task.id || `${Date.now()}-${Math.random()}`),
    title,
    completed: Boolean(task.completed),
    focusMinutes: bounded(task.focusMinutes, 0, 0, 10000000),
    createdAt: typeof task.createdAt === "string" ? task.createdAt : new Date().toISOString(),
    completedAt: typeof task.completedAt === "string" ? task.completedAt : "",
  };
}

function normalizeEnergy(value) {
  const energy = Number(value);
  if (!Number.isFinite(energy)) return 0;
  return Math.max(0, Math.min(5, Math.round(energy)));
}

function averageSessionEnergy(sessions) {
  const ratedSessions = sessions.filter((session) => session.energy > 0);
  if (!ratedSessions.length) return 0;
  return Math.round((ratedSessions.reduce((sum, session) => sum + session.energy, 0) / ratedSessions.length) * 10) / 10;
}

function sanitizeImportedSettings(settings) {
  const allowed = {};
  ["notifications", "tick", "wakeLock", "onboarded"].forEach((key) => {
    if (typeof settings[key] === "boolean") allowed[key] = settings[key];
  });
  if (typeof settings.preset === "string" && (PRESETS[settings.preset] || settings.preset === "custom")) allowed.preset = settings.preset;
  if (typeof settings.pet === "string" && PETS[settings.pet]) allowed.pet = settings.pet;
  if (typeof settings.customPetUrl === "string") allowed.customPetUrl = settings.customPetUrl;
  if (typeof settings.customPetSourceUrl === "string") allowed.customPetSourceUrl = settings.customPetSourceUrl;
  if (typeof settings.customPetLabel === "string") allowed.customPetLabel = settings.customPetLabel.slice(0, 80);
  if (settings.customPetMeta && typeof settings.customPetMeta === "object") {
    allowed.customPetMeta = normalizePetMeta(settings.customPetMeta);
  }
  if (typeof settings.currentIntention === "string") allowed.currentIntention = settings.currentIntention.slice(0, 80);
  if (typeof settings.activeTaskId === "string") allowed.activeTaskId = settings.activeTaskId;
  if (Number.isFinite(Number(settings.breakPromptIndex))) {
    allowed.breakPromptIndex = normalizeBreakPromptIndex(settings.breakPromptIndex);
  }
  const limits = { work: [1, 180], break: [1, 90], longBreak: [1, 120], interval: [0, 12], dailyGoalMinutes: [15, 720] };
  Object.entries(limits).forEach(([key, [min, max]]) => {
    if (typeof settings[key] === "number" && Number.isFinite(settings[key])) allowed[key] = bounded(settings[key], min, min, max);
  });
  return allowed;
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    "\"": "&quot;",
    "'": "&#39;",
  }[character]));
}

function escapeAttribute(value) {
  return escapeHtml(value);
}

async function shareSummary() {
  const text = buildSummaryText();
  try {
    if (navigator.share) {
      await navigator.share({ title: "Pomo Pet focus summary", text });
      setDataStatus("Summary shared.");
    } else if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text);
      setDataStatus("Summary copied.");
    } else {
      setDataStatus(text);
    }
  } catch {
    setDataStatus("Share cancelled.");
  }
}

function buildSummaryText() {
  const todaySessions = sessionsToday();
  const todayFocus = todaySessions.reduce((sum, session) => sum + session.focusMinutes, 0);
  const allFocus = state.stats.sessions.reduce((sum, session) => sum + session.focusMinutes, 0);
  const bond = computeBond(allFocus, todayFocus);
  const averageEnergy = averageSessionEnergy(todaySessions);
  const energyText = averageEnergy ? ` Average energy ${averageEnergy}/5.` : "";
  return `I focused ${todayFocus}m today with Pomo Pet. ${todaySessions.length} sessions, Level ${bond.level}, ${bond.goalPercent}% daily goal.${energyText}`;
}

function setDataStatus(message) {
  els.dataStatus.textContent = message;
}

function completeOnboarding() {
  state.settings.currentIntention = els.onboardingIntentionInput.value.trim();
  state.settings.onboarded = true;
  saveState();
  render();
}

function tick() {
  if (todayKey() !== renderedDay) { renderedDay = todayKey(); render(); }
  if (!state.timer.running) return;
  if (!hasControl) {
    state.timer.remaining = Math.max(0, Math.ceil((state.timer.deadline - Date.now()) / 1000));
    renderClock();
    return;
  }
  const remaining = Math.max(0, Math.ceil((state.timer.deadline - Date.now()) / 1000));
  if (remaining === state.timer.remaining && remaining > 0) return;
  state.timer.remaining = remaining;
  if (remaining === 0) completePhase();
  else {
    if (state.settings.tick && state.timer.phase === "work") playTick();
    renderClock();
  }
}

async function notifyPhase() {
  if (!state.settings.notifications || !("Notification" in window) || Notification.permission !== "granted") return;
  const title = state.timer.phase === "work" ? "Break is over" : "Session complete";
  try {
    const registration = await navigator.serviceWorker?.getRegistration();
    await registration?.showNotification(title, {
      body: state.timer.message,
      icon: "./assets/icons/icon-192.png",
      badge: "./assets/icons/icon-192.png",
    });
  } catch { /* Notification support varies by browser and permission policy. */ }
}

function unlockAudio() {
  if (!audioContext) {
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    if (!AudioContextClass) return;
    audioContext = new AudioContextClass();
  }
  if (audioContext.state === "suspended") audioContext.resume().catch(() => {});
}

function playTick() {
  if (!audioContext) return;
  const oscillator = audioContext.createOscillator();
  const gain = audioContext.createGain();
  oscillator.frequency.value = 520;
  gain.gain.value = 0.018;
  oscillator.connect(gain);
  gain.connect(audioContext.destination);
  oscillator.start();
  oscillator.stop(audioContext.currentTime + 0.018);
}

async function syncWakeLock() {
  const shouldHoldWakeLock = state.settings.wakeLock && state.timer.running && "wakeLock" in navigator;
  if (!shouldHoldWakeLock) {
    await releaseWakeLock();
    return;
  }
  if (wakeLock || wakeLockRequest || document.visibilityState !== "visible") return;
  try {
    wakeLockRequest = navigator.wakeLock.request("screen");
    wakeLock = await wakeLockRequest;
    wakeLock.addEventListener("release", () => {
      wakeLock = null;
    });
  } catch {
    wakeLock = null;
  } finally {
    wakeLockRequest = null;
  }
}

async function releaseWakeLock() {
  if (!wakeLock) return;
  const lock = wakeLock;
  wakeLock = null;
  try {
    await lock.release();
  } catch {
    // The lock may already have been released by the browser.
  }
}

function bindEvents() {
  els.startPauseButton.addEventListener("click", startPause);
  els.resetButton.addEventListener("click", () => resetTimer({ confirm: true }));
  els.skipButton.addEventListener("click", skipPhase);
  els.taskForm.addEventListener("submit", (event) => {
    event.preventDefault();
    addTask(els.taskInput.value);
  });
  els.onboardingIntentionInput.addEventListener("input", () => {
    state.settings.currentIntention = els.onboardingIntentionInput.value.trim();
    saveState();
    render();
  });
  els.onboardingStartButton.addEventListener("click", completeOnboarding);
  els.intentionInput.addEventListener("input", () => {
    state.settings.currentIntention = els.intentionInput.value.trim();
    const activeTask = state.stats.tasks.find((task) => task.id === state.settings.activeTaskId);
    if (!activeTask || activeTask.title !== state.settings.currentIntention) {
      state.settings.activeTaskId = "";
    }
    saveState();
    render();
  });
  bindNumberInput(els.workInput, "work", 1, 180);
  bindNumberInput(els.breakInput, "break", 1, 90);
  bindNumberInput(els.longBreakInput, "longBreak", 1, 120);
  bindNumberInput(els.intervalInput, "interval", 0, 12);
  bindNumberInput(els.dailyGoalInput, "dailyGoalMinutes", 15, 720);
  els.customPetInput.addEventListener("input", () => {
    scheduleCustomPetResolve();
  });
  els.tickToggle.addEventListener("change", () => updateSetting("tick", els.tickToggle.checked));
  els.wakeLockToggle.addEventListener("change", () => updateSetting("wakeLock", els.wakeLockToggle.checked));
  els.clearStatsButton.addEventListener("click", () => {
    if (!window.confirm("Clear all focus history? Export a backup first if you want to keep it. Your tasks and settings will stay.")) return;
    state.stats.sessions = [];
    state.stats.tasks.forEach((task) => { task.focusMinutes = 0; });
    state.timer.sessionsCompleted = 0;
    state.stats.bestStreak = 0;
    saveState();
    setDataStatus("Stats cleared.");
    render();
  });
  els.exportStatsButton.addEventListener("click", exportStats);
  els.importStatsButton.addEventListener("click", () => els.importStatsInput.click());
  els.importStatsInput.addEventListener("change", () => importStatsFromFile(els.importStatsInput.files?.[0]));
  els.shareSummaryButton.addEventListener("click", shareSummary);
  els.nextBreakPromptButton.addEventListener("click", nextBreakPrompt);
  els.completeActiveTaskButton.addEventListener("click", completeActiveTask);
  els.reviewRating.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-energy]");
    if (!button) return;
    reviewEnergy = normalizeEnergy(button.dataset.energy);
    renderSessionReview();
  });
  els.saveReviewButton.addEventListener("click", saveSessionReview);
  els.skipReviewButton.addEventListener("click", closeSessionReview);
  els.notificationToggle.addEventListener("change", requestNotifications);
  window.addEventListener("online", render);
  window.addEventListener("offline", render);
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "visible") {
      tick();
      renderClock();
      syncWakeLock();
    } else {
      releaseWakeLock();
    }
  });
}

function scheduleCustomPetResolve() {
  const value = els.customPetInput.value.trim();
  const version = ++petRequestVersion;
  window.clearTimeout(customPetResolveTimer);
  if (!value || (isDirectSpritesheetUrl(value) && !isCodexPetsUrl(value))) {
    setDirectCustomPet(value);
    return;
  }
  els.customPetStatus.textContent = "Resolving pet link...";
  customPetResolveTimer = window.setTimeout(() => resolveCustomPetInput(value, version), 450);
}

function setDirectCustomPet(url) {
  state.settings.customPetUrl = url;
  state.settings.customPetSourceUrl = "";
  state.settings.customPetLabel = "";
  state.settings.customPetMeta = null;
  els.customPetStatus.textContent = url ? "Using direct spritesheet." : "";
  saveState();
  render();
}

async function resolveCustomPetInput(value, version) {
  try {
    if (!isCodexPetsUrl(value)) {
      if (isDirectSpritesheetUrl(value)) setDirectCustomPet(value);
      else els.customPetStatus.textContent = "Use a direct spritesheet or Codex Pets link.";
      return;
    }
    const fallback = fallbackCodexPetFromUrl(value);
    applyResolvedCustomPet(value, fallback);
    if (typeof window.fetch === "function") {
      try {
        const resolved = await resolveCodexPetShare(value);
        if (version === petRequestVersion) applyResolvedCustomPet(value, resolved);
      } catch {
        // The browser can still render the fallback spritesheet URL even when API CORS is unavailable.
      }
    }
  } catch (error) {
    els.customPetStatus.textContent = `Could not load that Codex Pets link: ${error.message}`;
  }
}

function applyResolvedCustomPet(sourceUrl, resolved) {
  state.settings.customPetUrl = resolved.sprite;
  state.settings.customPetSourceUrl = sourceUrl;
  state.settings.customPetLabel = resolved.label;
  state.settings.customPetMeta = resolved.meta;
  els.customPetStatus.textContent = `Loaded ${resolved.label}.`;
  saveState();
  render();
}

function isDirectSpritesheetUrl(value) {
  try {
    const url = new URL(value);
    return url.protocol === "https:" && /\.(webp|png|gif)$/i.test(url.pathname);
  } catch { return false; }
}

function isRenderableSpriteUrl(value) {
  return isDirectSpritesheetUrl(value) || /^https:\/\/codex-pets\.net\/api\/pets\/[^/]+\/spritesheet(?:\?.*)?$/i.test(value);
}

function isCodexPetsUrl(value) {
  try {
    return new URL(value).protocol === "https:" && new URL(value).hostname === "codex-pets.net";
  } catch {
    return false;
  }
}

function fallbackCodexPetFromUrl(value) {
  const slug = codexPetSlugFromUrl(value);
  const directSprite = isDirectSpritesheetUrl(value) ? value : "";
  if (!slug) throw new Error("missing pet slug");
  return {
    sprite: directSprite || `https://codex-pets.net/api/pets/${encodeURIComponent(slug)}/spritesheet`,
    label: petLabelFromSlug(slug),
    meta: DEFAULT_PET_META,
  };
}

function codexPetSlugFromUrl(value) {
  const url = new URL(value);
  const shareMatch = url.pathname.match(/^\/share\/([^/?#]+)/);
  if (shareMatch) return decodeURIComponent(shareMatch[1]);
  const petMatch = url.pathname.match(/^\/pets\/([^/?#]+)/);
  if (petMatch) return decodeURIComponent(petMatch[1]);
  const apiMatch = url.pathname.match(/^\/api\/pets\/([^/?#]+)/);
  if (apiMatch) return decodeURIComponent(apiMatch[1]);
  const assetMatch = url.pathname.match(/^\/assets\/pets\/v\/[^/]+\/([^/?#]+)\//);
  if (assetMatch) return decodeURIComponent(assetMatch[1]);
  const hashMatch = url.hash.match(/^#\/pets\/([^/?#]+)/);
  if (hashMatch) return decodeURIComponent(hashMatch[1]);
  return "";
}

function petLabelFromSlug(slug) {
  const label = slug
    .split(/[-_]+/)
    .filter(Boolean)
    .map((part) => part[0]?.toUpperCase() + part.slice(1))
    .join(" ");
  if (!label) return "Codex pet";
  return label.replace(/ops\b/i, "Ops");
}

async function resolveCodexPetShare(url) {
  const slug = codexPetSlugFromUrl(url);
  if (!slug) throw new Error("missing pet slug");
  const apiPetMeta = await fetchPetJson(`https://codex-pets.net/api/pets/${encodeURIComponent(slug)}`).catch(() => ({}));
  const apiPet = apiPetMeta.pet || apiPetMeta;
  const sprite = spriteUrlFromPetMeta(apiPet, url, slug);
  const manifestUrl = petManifestUrlFromSprite(sprite);
  const manifestMeta = manifestUrl ? await fetchPetJson(manifestUrl).catch(() => ({})) : {};
  const petMeta = mergePetMeta(apiPet, manifestMeta);
  if (!hasPetManifestData(apiPet) && !hasPetManifestData(manifestMeta)) throw new Error("pet manifest unavailable");
  return {
    sprite: spriteUrlFromPetMeta(petMeta, url, slug),
    label: petMeta.displayName || petMeta.id || "custom pet",
    meta: normalizePetMeta(petMeta),
  };
}

async function fetchPetJson(url) {
  const response = await fetch(url, { headers: { accept: "application/json" }, signal: AbortSignal.timeout(8000) });
  if (!response.ok) throw new Error("pet manifest unavailable");
  return response.json();
}

function mergePetMeta(apiPet, manifestPet) {
  return {
    ...apiPet,
    ...manifestPet,
    validationReport: manifestPet.validationReport || apiPet.validationReport,
    spritesheetUrl: manifestPet.spritesheetUrl || apiPet.spritesheetUrl,
    displayName: manifestPet.displayName || apiPet.displayName,
    id: manifestPet.id || apiPet.id,
  };
}

function hasPetManifestData(meta) {
  return Boolean(meta.id || meta.displayName || meta.spritesheetUrl || meta.spritesheetPath || meta.validationReport || meta.frameWidth || meta.frameHeight);
}

function spriteUrlFromPetMeta(meta, sourceUrl, slug) {
  if (meta.spritesheetUrl) return absolutePetUrl(meta.spritesheetUrl, sourceUrl);
  if (meta.spritesheetPath && isDirectSpritesheetUrl(sourceUrl)) return absolutePetUrl(meta.spritesheetPath, sourceUrl);
  if (isDirectSpritesheetUrl(sourceUrl)) return sourceUrl;
  return `https://codex-pets.net/api/pets/${encodeURIComponent(slug)}/spritesheet`;
}

function petManifestUrlFromSprite(spriteUrl) {
  try {
    const url = new URL(spriteUrl);
    if (url.hostname !== "codex-pets.net" || !isDirectSpritesheetUrl(url.href)) return "";
    url.pathname = url.pathname.replace(/[^/]+$/, "pet.json");
    url.search = "";
    url.hash = "";
    return url.href;
  } catch {
    return "";
  }
}

function absolutePetUrl(path, sourceUrl) {
  try {
    return new URL(path, sourceUrl).href;
  } catch {
    return path;
  }
}

function normalizePetMeta(meta) {
  const cellSize = parseSize(meta.validationReport?.cellSize);
  const atlasSize = parseSize(meta.validationReport?.atlasSize);
  const frameWidth = positiveNumber(meta.frameWidth ?? cellSize?.width, DEFAULT_PET_META.frameWidth);
  const frameHeight = positiveNumber(meta.frameHeight ?? cellSize?.height, DEFAULT_PET_META.frameHeight);
  const animations = {};
  Object.entries(meta.animations || {}).forEach(([name, animation]) => {
    if (!animation || typeof animation !== "object") return;
    animations[name] = {
      row: positiveNumber(animation.row, 0),
      frames: positiveNumber(animation.frames, 1, 1),
      fps: positiveNumber(animation.fps, 8, 1),
    };
  });
  return {
    frameWidth,
    frameHeight,
    sheetWidth: positiveNumber(meta.sheetWidth ?? atlasSize?.width, frameWidth * Math.max(8, ...Object.values(animations).map((animation) => animation.frames)), 1),
    animations: Object.keys(animations).length ? animations : DEFAULT_PET_META.animations,
  };
}

function parseSize(value) {
  if (typeof value !== "string") return null;
  const match = value.match(/^(\d+)x(\d+)$/i);
  if (!match) return null;
  return { width: Number(match[1]), height: Number(match[2]) };
}

function positiveNumber(value, fallback, minimum = 0) {
  const number = Number(value);
  if (!Number.isFinite(number) || number < minimum || number > 16384) return fallback;
  return number;
}

function bindNumberInput(input, key, min, max) {
  const update = () => {
    const value = clampNumber(input, min, max);
    input.value = value;
    updateSetting(key, value);
  };
  input.addEventListener("change", update);
}

function clampNumber(input, min, max) {
  const value = Number.parseInt(input.value, 10);
  if (Number.isNaN(value)) return min;
  return Math.max(min, Math.min(max, value));
}

async function requestNotifications() {
  if (!("Notification" in window)) {
    state.settings.notifications = false;
    saveState();
    render();
    return;
  }

  if (els.notificationToggle.checked) {
    const permission = await Notification.requestPermission().catch(() => "denied");
    state.settings.notifications = permission === "granted";
  } else {
    state.settings.notifications = false;
  }
  saveState();
  render();
}

async function registerServiceWorker() {
  if (!("serviceWorker" in navigator)) {
    els.offlineStatus.textContent = "browser-only";
    return;
  }
  try {
    await navigator.serviceWorker.register("./sw.js");
  } catch {
    els.offlineStatus.textContent = "offline unavailable";
  }
}

bindEvents();
window.addEventListener("hashchange", syncRoute);
syncRoute();
render();
acquireControl();
registerServiceWorker();
ticker = window.setInterval(tick, 250);
window.addEventListener("pagehide", () => {
  window.clearInterval(ticker);
  releaseControl?.();
  releaseWakeLock();
});


// One editing tab prevents duplicate completions and stale tabs overwriting history.
async function acquireControl() {
  if (!("locks" in navigator) || controlRequest) return;
  const banner = document.querySelector("#storageNotice");
  banner.hidden = false;
  banner.textContent = "Connecting to your local workspace…";
  controlRequest = navigator.locks.request(STORAGE_KEY, async () => {
    hasControl = true;
    Object.assign(state, loadState());
    document.querySelectorAll("button, input, textarea").forEach((control) => { control.disabled = false; });
    banner.hidden = storage.isPersistent();
    banner.textContent = "Storage is unavailable. Export your work before closing this tab.";
    render();
    tick();
    await new Promise((resolve) => { releaseControl = resolve; });
    hasControl = false;
    controlRequest = null;
    releaseControl = null;
  });
  if (!hasControl) banner.textContent = "This workspace is open in another tab. You can browse here; close the other tab to edit here.";
}

window.addEventListener("storage", (event) => {
  if (event.key !== STORAGE_KEY || hasControl) return;
  Object.assign(state, loadState());
  render();
});
window.addEventListener("pageshow", (event) => {
  if (!event.persisted) return;
  acquireControl();
  window.clearInterval(ticker);
  ticker = window.setInterval(tick, 250);
  tick();
});

function syncDialog() {
  const next = !els.onboardingOverlay.hidden ? els.onboardingOverlay : !els.sessionReviewOverlay.hidden ? els.sessionReviewOverlay : null;
  document.querySelector(".app-shell").inert = Boolean(next);
  if (next === activeDialog) return;
  if (next) {
    dialogReturnFocus = document.activeElement;
    next.querySelector("input, textarea, button")?.focus();
  } else if (activeDialog) {
    if (dialogReturnFocus?.isConnected && dialogReturnFocus !== document.body) dialogReturnFocus.focus();
    else els.startPauseButton.focus();
  }
  activeDialog = next;
}

document.addEventListener("keydown", (event) => {
  if (activeDialog) {
    if (event.key === "Escape" && activeDialog === els.sessionReviewOverlay) closeSessionReview();
    if (event.key !== "Tab") return;
    const controls = [...activeDialog.querySelectorAll("button:not(:disabled), input:not(:disabled), textarea:not(:disabled)")];
    const first = controls[0], last = controls.at(-1);
    if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
    else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
    return;
  }
  if (!hasControl || event.repeat || event.ctrlKey || event.metaKey || event.altKey) return;
  if (event.code === "Space" && !event.target.closest("input, textarea, button, a, [contenteditable]")) {
    event.preventDefault();
    startPause();
  }
});
