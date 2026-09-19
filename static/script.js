// Browser storage keeps this class project simple: no database or accounts.
// sessionStorage holds the current recipe; localStorage holds saved recipes.
const CURRENT_KEY = 'pantry.current.v1';
const SAVED_KEY = 'pantry.saved.v1';
const DRAFT_KEY = 'pantry.draft.v1';
const errorMessage = document.querySelector('#error');
const statusMessage = document.querySelector('#status');

// Only local, curated image paths are used, never URLs supplied by the AI.
const FOOD_IMAGES = {
  chickpea: ['chickpea.jpg', 'Lemony chickpeas with tomatoes and spinach'],
  burger: ['burger.jpg', 'Cheeseburger with fries'],
  pasta: ['pasta.jpg', 'Tomato and basil pasta'],
  salad: ['salad.jpg', 'Colorful vegetable grain bowl'],
  ramen: ['ramen.jpg', 'Japanese shoyu ramen with noodles, pork, egg, and scallions'],
  curry: ['curry.jpg', 'Indian chana masala with basmati rice and roti'],
  tacos: ['tacos.jpg', 'Mexican chicken tacos with cilantro, salsa verde, and lime'],
  paella: ['paella.jpg', 'Spanish seafood paella with saffron rice, shrimp, and mussels'],
  general: ['salad.jpg', 'A colorful bowl for food inspiration'],
};

function recipeImage(recipe) {
  // Older saved recipes have no category; they still open normally.
  const category = Object.hasOwn(FOOD_IMAGES, recipe.image_category) ? recipe.image_category : 'general';
  return FOOD_IMAGES[category];
}

function servingLabel(recipe) {
  const count = recipe.servings || 2; // The original app always made 2 servings.
  return `${count} serving${count === 1 ? '' : 's'}`;
}

const galleryToggle = document.querySelector('#gallery-toggle');
if (galleryToggle) {
  const track = document.querySelector('#dish-track');
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  let paused = reducedMotion.matches;
  function updateGallery() {
    track.classList.toggle('is-paused', paused);
    galleryToggle.textContent = paused ? 'Play gallery' : 'Pause gallery';
    galleryToggle.setAttribute('aria-pressed', String(paused));
  }
  galleryToggle.addEventListener('click', () => { paused = !paused; updateGallery(); });
  reducedMotion.addEventListener('change', event => { paused = event.matches; updateGallery(); });
  updateGallery();
}

function showError(message) {
  errorMessage.textContent = message;
  errorMessage.hidden = false;
}

function readStorage(storage, key, fallback) {
  const text = storage.getItem(key);
  return text === null ? fallback : JSON.parse(text);
}

function isRecipeEntry(entry) {
  const recipe = entry?.recipe;
  return typeof entry?.id === 'string' && ['demo', 'live'].includes(entry.mode)
    && recipe && typeof recipe.name === 'string' && typeof recipe.description === 'string'
    && Number.isFinite(recipe.cooking_time_minutes)
    && Array.isArray(recipe.ingredients) && recipe.ingredients.every(item => typeof item === 'string')
    && Array.isArray(recipe.instructions) && recipe.instructions.every(item => typeof item === 'string');
}

function savedRecipes() {
  const recipes = readStorage(localStorage, SAVED_KEY, []);
  if (!Array.isArray(recipes) || !recipes.every(isRecipeEntry)) {
    throw new Error('Invalid saved recipe data');
  }
  return recipes;
}

function showList(selector, items) {
  const list = document.querySelector(selector);
  list.replaceChildren();
  items.forEach(item => {
    const li = document.createElement('li');
    li.textContent = item; // API and stored text are never treated as HTML.
    list.append(li);
  });
}

const form = document.querySelector('#recipe-form');
if (form) {
  const button = document.querySelector('#generate-button');
  try {
    const draft = readStorage(sessionStorage, DRAFT_KEY, {});
    Object.entries(draft).forEach(([key, value]) => {
      if (form.elements.namedItem(key)) form.elements.namedItem(key).value = value ?? '';
    });
  } catch {
    showError('Your previous form could not be restored. You can enter new ingredients below.');
  }

  document.querySelector('#sample-button').addEventListener('click', () => {
    form.elements.ingredients.value = 'chickpeas, cherry tomatoes, spinach, garlic, lemon';
    form.elements.dietary_restrictions.value = 'vegetarian';
    form.elements.max_time.value = '30';
    form.elements.equipment.value = 'stovetop, skillet';
    form.elements.cuisine.value = 'Mediterranean';
    form.elements.flavor_profile.value = 'Fresh & bright';
    form.elements.servings.value = '2';
    form.elements.difficulty.value = 'Easy';
    form.elements.ingredients.focus();
  });

  form.addEventListener('submit', async event => {
    event.preventDefault();
    errorMessage.hidden = true;
    statusMessage.textContent = '';
    const inputs = {
      ingredients: form.elements.ingredients.value.trim(),
      dietary_restrictions: form.elements.dietary_restrictions.value.trim(),
      max_time: form.elements.max_time.value ? Number(form.elements.max_time.value) : null,
      equipment: form.elements.equipment.value.trim(),
      cuisine: form.elements.cuisine.value,
      flavor_profile: form.elements.flavor_profile.value,
      servings: Number(form.elements.servings.value),
      difficulty: form.elements.difficulty.value,
    };
    if (!inputs.ingredients) {
      showError('Please enter at least one ingredient.');
      form.elements.ingredients.focus();
      return;
    }
    try {
      sessionStorage.setItem(DRAFT_KEY, JSON.stringify(inputs));
    } catch {
      showError('Browser storage is unavailable. Allow site storage to open recipes on a separate page.');
      return;
    }
    button.disabled = true;
    button.textContent = 'Preparing your recipe…';
    form.setAttribute('aria-busy', 'true');
    statusMessage.textContent = 'Sending your ingredients to the kitchen…';
    try {
      // 1. JAVASCRIPT SENDS THE USER’S INPUTS TO THE PYTHON BACKEND.
      // No API key is sent to or stored in the browser.
      const response = await fetch('/generate-recipe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(inputs),
        signal: AbortSignal.timeout(60000),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Unable to generate a recipe. Please try again.');
      const entry = { ...data, id: crypto.randomUUID() };
      if (!isRecipeEntry(entry)) throw new Error('The service returned an incomplete recipe. Please try again.');
      try {
        sessionStorage.setItem(CURRENT_KEY, JSON.stringify(entry));
      } catch {
        throw new Error('The recipe could not be stored for the next page. Free some browser storage and try again.');
      }
      window.location.assign('/recipe');
    } catch (error) {
      showError(error.name === 'TimeoutError' ? 'The request timed out. Please try again.' : error instanceof TypeError || error instanceof SyntaxError ? 'Could not reach the recipe service. Check that Flask is running and try again.' : error.message);
      statusMessage.textContent = '';
    } finally {
      button.disabled = false;
      button.textContent = 'Generate Recipe ↗';
      form.setAttribute('aria-busy', 'false');
    }
  });
}

// 6. JAVASCRIPT DISPLAYS THE RECIPE RETURNED BY FLASK ON ITS OWN PAGE.
function displayRecipe(entry) {
  const recipe = entry.recipe;
  document.querySelector('#recipe-label').textContent = entry.mode === 'demo' ? 'DEMO RECIPE · FIXED SAMPLE' : 'YOUR AI-GENERATED RECIPE';
  document.querySelector('#recipe-name').textContent = recipe.name;
  document.querySelector('#recipe-description').textContent = recipe.description;
  const [imageFile, imageAlt] = recipeImage(recipe);
  const photo = document.querySelector('#recipe-image');
  photo.src = `/static/images/${imageFile}`;
  photo.alt = `${imageAlt} — illustrative image, not an exact recipe photo`;
  document.querySelector('#recipe-time').textContent = `${recipe.cooking_time_minutes} min · ${servingLabel(recipe)}`;
  document.querySelector('#recipe-difficulty').textContent = recipe.difficulty || 'Difficulty not recorded';
  document.querySelector('#recipe-flavor').textContent = recipe.flavor_profile || 'Flavor not recorded';
  const nutrition = recipe.nutrition_per_serving;
  const nutritionGrid = document.querySelector('#nutrition-values');
  const nutrients = { calories: ['Calories', 'kcal'], protein_g: ['Protein', 'g'], carbs_g: ['Carbs', 'g'], fat_g: ['Fat', 'g'], fiber_g: ['Fiber', 'g'] };
  Object.entries(nutrients).forEach(([key, [label, unit]]) => {
    const tile = document.createElement('div');
    const value = document.createElement('strong');
    const caption = document.createElement('span');
    const amount = nutrition?.[key];
    value.textContent = Number.isFinite(amount) && amount >= 0 ? `${amount} ${unit}` : '—';
    caption.textContent = label;
    tile.append(value, caption);
    nutritionGrid.append(tile);
  });
  document.querySelector('#nutrition-note').textContent = !nutrition
    ? 'Nutrition was not recorded for this older recipe. Generate a new recipe to include estimates.'
    : entry.mode === 'demo' ? 'Sample estimates per serving. Actual values vary with ingredients and portions.'
    : 'AI estimates per serving, not verified nutrition data. Actual values vary with ingredients and portions.';
  document.querySelector('#sample-warning').hidden = entry.mode !== 'demo';
  showList('#recipe-ingredients', recipe.ingredients);
  showList('#recipe-instructions', recipe.instructions);
  const received = document.querySelector('#received-inputs');
  const labels = { ingredients: 'Ingredients', dietary_restrictions: 'Dietary restrictions', max_time: 'Maximum time (minutes)', equipment: 'Equipment', cuisine: 'Cuisine', servings: 'Requested servings', flavor_profile: 'Requested flavor', difficulty: 'Requested difficulty' };
  Object.entries(labels).forEach(([key, label]) => {
    const term = document.createElement('dt');
    const value = document.createElement('dd');
    term.textContent = label;
    value.textContent = entry.received_inputs?.[key] || 'Not specified';
    received.append(term, value);
  });
  document.querySelector('#recipe').hidden = false;
  document.title = `${recipe.name} · Pantry & Plate`;
  const saveButton = document.querySelector('#save-button');
  function updateSaveButton() {
    try {
      const saved = savedRecipes().some(item => item.id === entry.id);
      saveButton.disabled = saved;
      saveButton.textContent = saved ? '♥ Saved to your recipes' : '♡ Save recipe';
    } catch {
      showError('Saved recipes could not be read. Check that browser storage is enabled.');
    }
  }
  saveButton.addEventListener('click', () => {
    errorMessage.hidden = true;
    try {
      const recipes = savedRecipes();
      if (!recipes.some(item => item.id === entry.id)) {
        recipes.unshift(entry);
        localStorage.setItem(SAVED_KEY, JSON.stringify(recipes));
      }
      updateSaveButton();
      statusMessage.textContent = 'Recipe saved. Find it in Saved recipes anytime in this browser.';
    } catch {
      showError('Could not save this recipe. Browser storage may be full or disabled. Your existing saved recipes have not been overwritten.');
    }
  });
  updateSaveButton();
  window.addEventListener('storage', event => {
    if (event.key === SAVED_KEY || event.key === null) updateSaveButton();
  });
}

if (document.querySelector('#recipe')) {
  try {
    const id = new URLSearchParams(window.location.search).get('id');
    const entry = id ? savedRecipes().find(item => item.id === id) : readStorage(sessionStorage, CURRENT_KEY, null);
    if (isRecipeEntry(entry)) displayRecipe(entry);
    else document.querySelector('#missing-recipe').hidden = false;
  } catch {
    document.querySelector('#missing-recipe').hidden = false;
    showError('This recipe could not be loaded from browser storage.');
  }
}

function renderSavedRecipes() {
  const list = document.querySelector('#saved-list');
  try {
    const recipes = savedRecipes();
    list.replaceChildren();
    document.querySelector('#saved-empty').hidden = recipes.length !== 0;
    recipes.forEach(entry => {
      const card = document.createElement('article');
      card.className = 'form-card saved-card';
      const photoLink = document.createElement('a');
      photoLink.className = 'saved-photo';
      photoLink.href = `/recipe?id=${encodeURIComponent(entry.id)}`;
      photoLink.setAttribute('aria-label', `Open ${entry.recipe.name}`);
      const photo = document.createElement('img');
      const [imageFile, imageAlt] = recipeImage(entry.recipe);
      photo.src = `/static/images/${imageFile}`;
      photo.alt = `${imageAlt} (illustrative)`;
      photo.loading = 'lazy';
      photo.width = 600;
      photo.height = 400;
      const photoCaption = document.createElement('span');
      photoCaption.textContent = 'Illustrative image';
      photoLink.append(photo, photoCaption);
      const body = document.createElement('div');
      body.className = 'saved-card-body';
      const label = document.createElement('p');
      label.className = 'eyebrow';
      label.textContent = entry.mode === 'demo' ? 'DEMO · FIXED SAMPLE' : 'AI-GENERATED RECIPE';
      const heading = document.createElement('h2');
      const link = document.createElement('a');
      link.href = `/recipe?id=${encodeURIComponent(entry.id)}`;
      link.textContent = entry.recipe.name;
      heading.append(link);
      const description = document.createElement('p');
      description.textContent = entry.recipe.description;
      const time = document.createElement('p');
      time.className = 'card-meta';
      time.textContent = `${entry.recipe.cooking_time_minutes} min · ${servingLabel(entry.recipe)}${entry.recipe.difficulty ? ` · ${entry.recipe.difficulty}` : ''}`;
      const calories = entry.recipe.nutrition_per_serving?.calories;
      if (Number.isFinite(calories)) time.textContent += ` · ~${calories} kcal/serving`;
      const remove = document.createElement('button');
      remove.className = 'text-button';
      remove.textContent = 'Remove from saved';
      remove.setAttribute('aria-label', `Remove ${entry.recipe.name} from saved recipes`);
      remove.addEventListener('click', () => {
        try {
          // Read again so removing one item does not overwrite changes from another tab.
          localStorage.setItem(SAVED_KEY, JSON.stringify(savedRecipes().filter(item => item.id !== entry.id)));
          errorMessage.hidden = true;
          renderSavedRecipes();
          statusMessage.textContent = 'Recipe removed from your saved list.';
        } catch {
          showError('Could not remove this recipe. Please check browser storage settings.');
        }
      });
      body.append(label, heading, description, time, remove);
      card.append(photoLink, body);
      list.append(card);
    });
  } catch {
    showError('Saved recipes could not be loaded. Browser storage may be disabled or contain unreadable data.');
  }
}

if (document.querySelector('#saved-list')) {
  renderSavedRecipes();
  window.addEventListener('storage', event => {
    if (event.key === SAVED_KEY || event.key === null) renderSavedRecipes();
  });
}
