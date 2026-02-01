import { generateItinerary, type Event, type ScoredEvent, type Constraints } from "./api";

const FLAVOR_TEXTS = [
  "Wandering through hidden gems\u2026",
  "Charting your perfect day\u2026",
  "Asking the locals for tips\u2026",
  "Finding the best-kept secrets\u2026",
  "Mapping out your adventure\u2026",
  "Curating moments worth remembering\u2026",
  "Discovering something special\u2026",
  "Plotting the scenic route\u2026",
];

let flavorInterval: ReturnType<typeof setInterval> | null = null;

function showLoading() {
  const overlay = document.getElementById("loading-overlay");
  const flavorEl = document.getElementById("loading-flavor");
  if (!overlay || !flavorEl) return;

  let index = Math.floor(Math.random() * FLAVOR_TEXTS.length);
  flavorEl.textContent = FLAVOR_TEXTS[index];
  overlay.classList.remove("hidden");
  flavorInterval = setInterval(() => {
    index = (index + 1) % FLAVOR_TEXTS.length;
    flavorEl.textContent = FLAVOR_TEXTS[index];
    flavorEl.style.animation = "none";
    flavorEl.offsetHeight; // trigger reflow
    flavorEl.style.animation = "";
  }, 3000);
}

function hideLoading() {
  const overlay = document.getElementById("loading-overlay");
  if (overlay) overlay.classList.add("hidden");
  if (flavorInterval) clearInterval(flavorInterval);
  flavorInterval = null;
}

type RatingState = {
  ratings: Record<string, number>;
  comparisons: number;
};

type Activity = Event & { name: string; address: string };

const STORAGE_KEY = "ranking-preferences-v1";
const DEFAULT_RATING = 1000;
const K_FACTOR = 24;

const pageRoot = document.querySelector<HTMLElement>("main[data-activities]");

if (pageRoot) {
  const raw = localStorage.getItem("unserious-activities");
  if (!raw) {
    window.location.href = "/constraints";
  } else {
    const activities = parseActivities(raw);
    if (activities.length >= 2) {
      initializeRanking(pageRoot, activities);
    }
  }
}

function parseActivities(payload: string): Activity[] {
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

  // --- Generate Itinerary ---
  const genBtn = document.getElementById("generate-itinerary-btn") as HTMLButtonElement | null;
  const genError = document.getElementById("ranking-error");

  if (genBtn) {
    genBtn.addEventListener("click", async () => {
      if (genError) genError.classList.add("hidden");

      const constraintsRaw = localStorage.getItem("unserious-constraints");
      if (!constraintsRaw) {
        window.location.href = "/constraints";
        return;
      }

      const constraints: Constraints = JSON.parse(constraintsRaw);

      // Normalize Elo ratings to 0–1 scores
      const ratings = state.ratings;
      const names = Object.keys(ratings);
      const values = names.map((n) => ratings[n]);
      const min = Math.min(...values, DEFAULT_RATING);
      const max = Math.max(...values, DEFAULT_RATING);
      const range = max - min || 1;

      const scoredEvents: ScoredEvent[] = activities.map((a) => ({
        event: {
          name: a.name,
          description: a.description ?? "",
          address: a.address,
          website: a.website ?? "",
          image: a.image ?? "",
          cost: a.cost ?? "",
          category: a.category ?? "",
        },
        score: ((ratings[a.name] ?? DEFAULT_RATING) - min) / range,
      }));

      genBtn.disabled = true;
      genBtn.textContent = "Generating itinerary\u2026";
      showLoading();

      try {
        const itinerary = await generateItinerary(constraints, scoredEvents);
        localStorage.setItem("unserious-itinerary", JSON.stringify(itinerary));
        window.location.href = "/itinerary";
      } catch (err) {
        hideLoading();
        if (genError) {
          genError.textContent =
            err instanceof Error ? err.message : "Something went wrong. Please try again.";
          genError.classList.remove("hidden");
        }
        genBtn.disabled = false;
        genBtn.textContent = "Generate Itinerary";
      }
    });
  }
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
    const category = card.querySelector<HTMLElement>("[data-category]");
    const cost = card.querySelector<HTMLElement>("[data-cost]");
    const website = card.querySelector<HTMLAnchorElement>("[data-website]");
    const websiteWrapper = card.querySelector<HTMLElement>("[data-website-wrapper]");
    const description = card.querySelector<HTMLElement>("[data-description]");
    if (!activity || !title || !address || !image) {
      return;
    }
    title.textContent = activity.name;
    address.textContent = activity.address;
    image.style.backgroundImage = `url(${getImageUrl(activity)})`;
    image.setAttribute("aria-label", `${activity.name} photo`);

    if (category) {
      const cat = (activity as any).category;
      if (cat) {
        category.textContent = cat;
        category.classList.remove("hidden");
      } else {
        category.classList.add("hidden");
      }
    }

    if (cost) {
      const c = (activity as any).cost;
      cost.textContent = c ? `💲 ${c}` : "";
    }

    if (website && websiteWrapper) {
      const url = (activity as any).website;
      if (url) {
        try {
          website.textContent = new URL(url).hostname;
        } catch {
          website.textContent = url;
        }
        website.setAttribute("href", url);
        websiteWrapper.classList.remove("hidden");
      } else {
        websiteWrapper.classList.add("hidden");
      }
    }

    if (description) {
      const desc = (activity as any).description;
      description.textContent = desc ?? "";
    }
  });
}

function updateStats(countEl: HTMLElement, state: RatingState) {
  countEl.textContent = state.comparisons.toString();
}

function getImageUrl(activity: Activity) {
  if (activity.image) {
    return activity.image;
  }
  const text = encodeURIComponent(activity.name);
  return `https://placehold.co/600x420/edd9c9/2b2623?text=${text}`;
}
