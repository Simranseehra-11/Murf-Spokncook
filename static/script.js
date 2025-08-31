const ingredientInput = document.getElementById("ingredientInput");
const findRecipesBtn = document.getElementById("findRecipesBtn");
const recipeList = document.getElementById("recipeList");
const recipeBox = document.getElementById("recipeBox");
const recipeTitle = document.getElementById("recipeTitle");
const recipeSteps = document.getElementById("recipeSteps");
const speakBtn = document.getElementById("speakBtn");
const voiceSelect = document.getElementById("voiceSelect");
const audioSection = document.getElementById("audioSection");
const audioPlayer = document.getElementById("audioPlayer");
const downloadLink = document.getElementById("downloadLink");
const logBox = document.getElementById("logBox");

// Log helper
function log(msg) {
  logBox.textContent += "\n" + msg;
}

// Load voices on page load
window.addEventListener("DOMContentLoaded", async () => {
  try {
    const res = await fetch("/api/voices");
    if (!res.ok) throw new Error("Failed to fetch voices");

    const voices = await res.json();
    voiceSelect.innerHTML = "";

    voices.forEach(voice => {
      const opt = document.createElement("option");
      opt.value = voice.voiceId;
      opt.textContent = `${voice.displayName} (${voice.locale})`;
      voiceSelect.appendChild(opt);
    });

    log(`🎙️ Loaded ${voices.length} voices.`);
  } catch (err) {
    voiceSelect.innerHTML = "<option value=''>Error loading voices</option>";
    log("❌ Voice load error: " + err.message);
  }
});

// Search recipes by ingredients
findRecipesBtn.addEventListener("click", async () => {
  const ingredients = ingredientInput.value.trim();
  if (!ingredients) {
    alert("Please enter some ingredients!");
    return;
  }

  try {
    const res = await fetch("/api/recipes", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ingredients })
    });

    if (!res.ok) throw new Error("Failed to fetch recipes");

    const data = await res.json();
    recipeList.innerHTML = "";

    if (data.recipes && data.recipes.length > 0) {
      data.recipes.forEach(r => {
        const li = document.createElement("li");
        li.textContent = r.title;
        li.style.cursor = "pointer";
        li.addEventListener("click", () => showRecipe(r));
        recipeList.appendChild(li);
      });
      log(`✅ Found ${data.recipes.length} matching recipe(s).`);
    } else {
      recipeList.innerHTML = "<li>No matching recipes found.</li>";
      log("ℹ️ No matches.");
    }
  } catch (err) {
    log("❌ Error: " + err.message);
  }
});

// Show recipe details
function showRecipe(recipe) {
  recipeTitle.textContent = recipe.title;
  recipeSteps.innerHTML = "";
  recipe.steps.forEach(step => {
    const li = document.createElement("li");
    li.textContent = step;
    recipeSteps.appendChild(li);
  });
  recipeBox.style.display = "block";
  audioSection.style.display = "block"; // ensure audio section is visible
}

// TTS with selected voice
speakBtn.addEventListener("click", async () => {
  const recipeText = [...recipeSteps.querySelectorAll("li")]
    .map(li => li.textContent)
    .join(". ");
  const selectedVoice = voiceSelect.value || "en-UK-Hazel";

  if (!recipeText) {
    alert("No recipe steps to read!");
    return;
  }

  log(`🗣️ Sending to TTS with voice: ${selectedVoice}`);
  try {
    const res = await fetch("/api/tts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: recipeText, voiceId: selectedVoice })
    });

    if (!res.ok) throw new Error("Failed to fetch TTS");

    const ct = res.headers.get("Content-Type") || "";
    if (ct.includes("application/json")) {
      const json = await res.json();
      if (json.audioUrl) {
        audioPlayer.src = json.audioUrl;
        downloadLink.href = json.audioUrl;
      } else {
        throw new Error("No audio URL in response");
      }
    } else {
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      audioPlayer.src = url;
      downloadLink.href = url;
    }

    audioSection.style.display = "block";
    log("✅ Recipe audio ready!");
  } catch (err) {
    log("❌ Error: " + err.message);
  }
});