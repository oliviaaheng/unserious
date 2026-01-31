type RatingState = {
  ratings: Record<string, number>;
  comparisons: number;
};

type Activity = {
  name: string;
  address: string;
};

const STORAGE_KEY = "ranking-preferences-v1";
const DEFAULT_RATING = 1000;
const K_FACTOR = 24;

const pageRoot = document.querySelector<HTMLElement>("main[data-activities]");

if (pageRoot) {
  const activities = parseActivities(pageRoot.dataset.activities);
  if (activities.length >= 2) {
    initializeRanking(pageRoot, activities);
  }
}

function parseActivities(payload?: string): Activity[] {
  if (!payload) {
    return [];
  }
  try {
    const parsed = JSON.parse(payload);
    if (!Array.isArray(parsed)) {
      return [];
    }
    return parsed.filter(isActivity);
  } catch {
    return [];
  }
}

function isActivity(value: unknown): value is Activity {
  if (!value || typeof value !== "object") {
    return false;
  }
  const candidate = value as Activity;
  return typeof candidate.name === "string" && typeof candidate.address === "string";
}

function initializeRanking(root: HTMLElement, activities: Activity[]) {
  const pairSection = root.querySelector<HTMLElement>("[data-pair]");
  const cards = pairSection ? [...pairSection.querySelectorAll<HTMLElement>("[data-card]")] : [];
  const countEl = root.querySelector<HTMLElement>("[data-count]");
  const resetButton = root.querySelector<HTMLButtonElement>("[data-reset]");

  if (!pairSection || cards.length < 2 || !countEl || !resetButton) {
    return;
  }

  const state = loadState();
  let currentPair = pickPair(activities);

  renderPair(currentPair, cards);
  updateStats(countEl, state);

  cards.forEach((card) => {
    card.addEventListener("click", () => {
      const choice = card.dataset.choice;
      const winner = choice === "a" ? currentPair[0] : currentPair[1];
      const loser = choice === "a" ? currentPair[1] : currentPair[0];
      updateRatings(state, winner.name, loser.name);
      currentPair = pickPair(activities, winner.name);
      renderPair(currentPair, cards);
      updateStats(countEl, state);
    });
  });

  resetButton.addEventListener("click", () => {
    state.ratings = {};
    state.comparisons = 0;
    persistState(state);
    currentPair = pickPair(activities);
    renderPair(currentPair, cards);
    updateStats(countEl, state);
  });
}

function loadState(): RatingState {
  const stored = localStorage.getItem(STORAGE_KEY);
  if (!stored) {
    return { ratings: {}, comparisons: 0 };
  }
  try {
    const parsed = JSON.parse(stored);
    return {
      ratings: parsed.ratings ?? {},
      comparisons: parsed.comparisons ?? 0,
    };
  } catch {
    return { ratings: {}, comparisons: 0 };
  }
}

function persistState(state: RatingState) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

function getRating(state: RatingState, name: string) {
  if (!(name in state.ratings)) {
    state.ratings[name] = DEFAULT_RATING;
  }
  return state.ratings[name];
}

function updateRatings(state: RatingState, winner: string, loser: string) {
  const winnerRating = getRating(state, winner);
  const loserRating = getRating(state, loser);
  const expectedWinner = 1 / (1 + 10 ** ((loserRating - winnerRating) / 400));
  const expectedLoser = 1 - expectedWinner;
  state.ratings[winner] = Math.round(winnerRating + K_FACTOR * (1 - expectedWinner));
  state.ratings[loser] = Math.round(loserRating + K_FACTOR * (0 - expectedLoser));
  state.comparisons += 1;
  persistState(state);
}

function pickPair(activities: Activity[], preferredName?: string): [Activity, Activity] {
  const shuffled = [...activities].sort(() => 0.5 - Math.random());
  let first = shuffled[0];
  let second = shuffled.find((item) => item.name !== first.name) ?? shuffled[1];
  if (preferredName && first.name === preferredName) {
    [first, second] = [second, first];
  }
  return [first, second];
}

function renderPair(pair: [Activity, Activity], cards: HTMLElement[]) {
  const [first, second] = pair;
  const pairs = [first, second];
  cards.forEach((card, index) => {
    const activity = pairs[index];
    const title = card.querySelector<HTMLElement>("[data-title]");
    const address = card.querySelector<HTMLElement>("[data-address]");
    const image = card.querySelector<HTMLElement>("[data-image]");
    if (!activity || !title || !address || !image) {
      return;
    }
    title.textContent = activity.name;
    address.textContent = activity.address;
    image.style.backgroundImage = `url(${getImageUrl(activity.name)})`;
    image.setAttribute("aria-label", `${activity.name} photo placeholder`);
  });
}

function updateStats(countEl: HTMLElement, state: RatingState) {
  countEl.textContent = state.comparisons.toString();
}

function getImageUrl(name: string) {
  const text = encodeURIComponent(name);
  return `https://placehold.co/600x420/edd9c9/2b2623?text=${text}`;
}
