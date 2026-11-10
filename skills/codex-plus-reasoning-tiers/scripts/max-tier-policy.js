// Native metadata is the input to catalog generation. UI metadata is not.
(() => {
  "use strict";
  const policyKey = "__codexPlusMaxTierPolicy";
  if (window[policyKey]) return;
  const bridgeKey = "__codexSessionDeleteBridge";
  const targetModels = ["deepseek-v4.1-flash-1017", "gpt-6.1-terra"];
  const order = ["none", "minimal", "low", "medium", "high", "xhigh", "max", "ultra"];
  const descriptions = {
    low: "Fast responses with lighter reasoning",
    medium: "Balances speed and reasoning depth for everyday tasks",
    high: "Greater reasoning depth for complex problems",
    xhigh: "Extra high reasoning depth for complex problems",
    max: "Maximum reasoning depth for the hardest problems",
  };

  function nativeEntry(entry = {}) {
    const updated = { ...entry };
    const levels = Array.isArray(entry.supported_reasoning_levels)
      ? entry.supported_reasoning_levels
      : Array.isArray(entry.supportedReasoningEfforts)
        ? entry.supportedReasoningEfforts.map((item) => ({
          effort: item.reasoningEffort, description: item.description || "",
        }))
        : ["low", "medium", "high", "xhigh"].map((effort) => ({
          effort, description: descriptions[effort],
        }));
    const unique = new Map();
    for (const item of levels) {
      if (item && typeof item.effort === "string" && !unique.has(item.effort)) {
        unique.set(item.effort, { ...item });
      }
    }
    if (!unique.has("max")) {
      unique.set("max", { effort: "max", description: descriptions.max });
    }
    const rank = (effort) => order.includes(effort) ? order.indexOf(effort) : order.length;
    updated.supported_reasoning_levels = [...unique.values()]
      .sort((a, b) => rank(a.effort) - rank(b.effort));
    const defaultLevel = entry.default_reasoning_level || entry.defaultReasoningEffort || "max";
    updated.default_reasoning_level = unique.has(defaultLevel) ? defaultLevel : "max";
    if (!updated.display_name && entry.displayName) updated.display_name = entry.displayName;
    delete updated.displayName;
    delete updated.defaultReasoningEffort;
    delete updated.supportedReasoningEfforts;
    return updated;
  }

  function profileRules(profile) {
    let metadata;
    try {
      metadata = JSON.parse(profile.modelMetadata || "{}");
      if (!metadata || typeof metadata !== "object" || Array.isArray(metadata)) throw new Error();
      for (const [key, entry] of Object.entries(metadata)) {
        if (targetModels.includes(key.toLowerCase())
            && entry && (typeof entry !== "object" || Array.isArray(entry))) {
          throw new Error();
        }
      }
    } catch {
      throw new Error(`Invalid modelMetadata for profile ${profile.id || "(unnamed)"}`);
    }
    const before = JSON.stringify(metadata);
    for (const slug of targetModels) {
      let entry = metadata[slug];
      for (const key of Object.keys(metadata)) {
        if (key !== slug && key.toLowerCase() === slug) {
          entry = { ...entry, ...metadata[key] };
          delete metadata[key];
        }
      }
      metadata[slug] = nativeEntry(entry);
    }
    if (JSON.stringify(metadata) === before) return profile;
    return { ...profile, modelMetadata: JSON.stringify(metadata) };
  }

  function settingsRules(settings) {
    if (!Array.isArray(settings?.relayProfiles)) return { value: settings, changed: 0 };
    let changed = 0;
    const profiles = settings.relayProfiles.map((profile) => {
      const updated = profileRules(profile);
      if (updated !== profile) changed++;
      return updated;
    });
    return {
      value: changed ? { ...settings, relayProfiles: profiles } : settings,
      changed,
    };
  }

  function catalogRules(catalog) {
    if (!Array.isArray(catalog?.models)) return catalog;
    const metadata = { ...(catalog.modelMetadata || catalog.model_metadata || {}) };
    const models = catalog.models.map((model) => {
      const slug = typeof model === "string" ? model : model?.slug;
      if (!targetModels.includes(slug)) return model;
      const entry = nativeEntry(typeof model === "object" ? model : metadata[slug]);
      metadata[slug] = {
        ...metadata[slug],
        displayName: metadata[slug]?.displayName || entry.display_name || slug,
        description: metadata[slug]?.description || entry.description || slug,
        defaultReasoningEffort: entry.default_reasoning_level,
        supportedReasoningEfforts: entry.supported_reasoning_levels.map((level) => ({
          reasoningEffort: level.effort, description: level.description || "",
        })),
      };
      return typeof model === "object" ? entry : model;
    });
    return { ...catalog, models, modelMetadata: metadata };
  }

  const descriptor = Object.getOwnPropertyDescriptor(window, bridgeKey);
  let original = window[bridgeKey];
  if (typeof original !== "function" || descriptor?.configurable === false) {
    throw new Error("Codex++ bridge is unavailable for the max-tier policy");
  }
  const state = {
    version: "1.0.1",
    targetModels: [...targetModels],
    repairedProfiles: 0,
    writes: 0,
    lastError: "",
  };
  let queue = Promise.resolve();
  let disposed = false;
  const enqueue = (operation) => {
    const result = queue.then(operation);
    queue = result.catch(() => {});
    return result;
  };
  const recordError = (error) => { state.lastError = String(error.message || error); };

  async function repairRead(payload = {}) {
    const settings = await original.call(window, "/settings/get", payload);
    if (disposed) return settings;
    let updated;
    try {
      updated = settingsRules(settings);
    } catch (error) {
      recordError(error);
      return settings;
    }
    if (!updated.changed) return settings;
    const saved = await original.call(window, "/settings/set", {
      relayProfiles: updated.value.relayProfiles,
    });
    if (saved?.status === "failed" || saved?.error) {
      throw new Error("Codex++ rejected native reasoning metadata");
    }
    state.repairedProfiles += updated.changed;
    state.writes++;
    state.lastError = "";
    return saved;
  }

  function wrapped(route, payload = {}) {
    if (route === "/settings/get") return enqueue(() => repairRead(payload));
    if (route === "/settings/set") {
      return enqueue(async () => {
        let updated;
        try {
          updated = settingsRules(payload);
        } catch (error) {
          recordError(error);
          return original.call(window, route, payload);
        }
        return original.call(window, route, updated.value);
      });
    }
    if (route === "/codex-model-catalog" || route === "/codex-config-model") {
      return Promise.resolve(original.call(window, route, payload)).then(catalogRules);
    }
    return original.call(window, route, payload);
  }

  // Reconnection may replace the bridge without replacing the document.
  const getter = () => wrapped;
  Object.defineProperty(window, bridgeKey, {
    configurable: true,
    enumerable: descriptor?.enumerable ?? true,
    get: getter,
    set(next) { if (next !== wrapped) original = next; },
  });
  state.sync = () => enqueue(async () => {
    const settings = await repairRead();
    return {
      profiles: settings?.relayProfiles?.length || 0,
      repairedProfiles: state.repairedProfiles,
      writes: state.writes,
      lastError: state.lastError,
    };
  });
  window[policyKey] = state;
  state.ready = state.sync().catch((error) => {
    recordError(error);
    return { lastError: state.lastError };
  });
  window.codexPlus?.onCleanup(() => {
    disposed = true;
    if (Object.getOwnPropertyDescriptor(window, bridgeKey)?.get === getter) {
      Object.defineProperty(window, bridgeKey, {
        configurable: descriptor?.configurable ?? true,
        enumerable: descriptor?.enumerable ?? true,
        writable: descriptor?.writable ?? true,
        value: original,
      });
    }
    if (window[policyKey] === state) delete window[policyKey];
  });
})();
