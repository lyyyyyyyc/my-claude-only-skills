const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const policyPath = path.join(__dirname, "max-tier-policy.js");
const source = fs.existsSync(policyPath) ? fs.readFileSync(policyPath, "utf8") : "";
const targets = ["deepseek-v4.1-flash-1017", "gpt-6.1-terra"];
const clone = (value) => JSON.parse(JSON.stringify(value));

function harness(profiles = [], catalog = { models: [] }) {
  let settings = { activeRelayId: profiles[0]?.id, relayProfiles: clone(profiles) };
  const writes = [];
  const cleanups = [];
  const original = async (route, payload = {}) => {
    if (route === "/settings/get") return clone(settings);
    if (route === "/settings/set") {
      writes.push(clone(payload));
      settings = { ...settings, ...clone(payload) };
      return clone(settings);
    }
    if (route === "/codex-model-catalog") return clone(catalog);
    return { route, payload };
  };
  const window = {
    __codexSessionDeleteBridge: original,
    codexPlus: { onCleanup: (cleanup) => cleanups.push(cleanup) },
  };
  const context = vm.createContext({ window, console });
  vm.runInContext(source, context);
  return {
    window, original, writes, cleanups,
    settings: () => clone(settings),
    replaceSettings: (value) => { settings = clone(value); },
    ready: () => window.__codexPlusMaxTierPolicy?.ready ?? Promise.resolve(),
  };
}

test("all profiles receive native catalog fields, including future model selections", async () => {
  const profiles = [
    { id: "one", modelList: targets[0], authContents: "unchanged-secret-fixture" },
    { id: "two", modelList: targets[1], contextWindow: "1000000" },
    { id: "three", modelList: "another-model" },
  ];
  const app = harness(profiles);
  await app.ready();
  for (const profile of app.settings().relayProfiles) {
    const metadata = JSON.parse(profile.modelMetadata || "{}");
    for (const slug of targets) {
      assert.ok(metadata[slug]?.supported_reasoning_levels?.some((item) => item.effort === "max"),
        `${profile.id}/${slug}: native max override is missing`);
    }
  }
  assert.equal(app.settings().relayProfiles[0].authContents, profiles[0].authContents);
  assert.equal(app.settings().relayProfiles[1].contextWindow, "1000000");
  assert.equal(app.settings().relayProfiles[2].modelList, "another-model");
});

test("legacy UI metadata is migrated, preserving unrelated native overrides", async () => {
  const app = harness([{
    id: "legacy",
    modelMetadata: JSON.stringify({
      [targets[0]]: {
        displayName: "DeepSeek snapshot",
        defaultReasoningEffort: "max",
        supportedReasoningEfforts: [{ reasoningEffort: "high", description: "Existing high" }],
        supports_image_detail_original: true,
      },
      "another-model": { description: "Keep me", custom_flag: 37 },
    }),
  }]);
  await app.ready();
  const metadata = JSON.parse(app.settings().relayProfiles[0].modelMetadata);
  const entry = metadata[targets[0]];
  assert.equal(entry.display_name, "DeepSeek snapshot");
  assert.equal(entry.default_reasoning_level, "max");
  assert.equal(entry.supports_image_detail_original, true);
  assert.equal(entry.supportedReasoningEfforts, undefined);
  assert.deepEqual(metadata["another-model"], { description: "Keep me", custom_flag: 37 });
  assert.deepEqual(entry.supported_reasoning_levels.map((level) => level.effort), ["high", "max"]);
});

test("native defaults and extra efforts are preserved without duplicates", async () => {
  const app = harness([{
    id: "native",
    modelMetadata: JSON.stringify({
      [targets[1]]: {
        default_reasoning_level: "high",
        supported_reasoning_levels: [
          { effort: "ultra", description: "Keep ultra" },
          { effort: "high", description: "Keep high" },
          { effort: "max", description: "Keep max" },
          { effort: "max", description: "Duplicate" },
        ],
      },
    }),
  }]);
  await app.ready();
  const entry = JSON.parse(app.settings().relayProfiles[0].modelMetadata)[targets[1]];
  assert.equal(entry.default_reasoning_level, "high");
  assert.deepEqual(entry.supported_reasoning_levels.map((level) => level.effort),
    ["high", "max", "ultra"]);
});

test("repeated settings reads do not repeatedly rewrite settings", async () => {
  const app = harness([{ id: "repeat", modelList: targets.join("\n") }]);
  await app.ready();
  assert.equal(app.writes.length, 1);
  for (let index = 0; index < 8; index++) {
    await app.window.__codexSessionDeleteBridge("/settings/get", {});
  }
  assert.equal(app.writes.length, 1);
});

test("a newly created provider is repaired on the next settings read", async () => {
  const app = harness([{ id: "old" }]);
  await app.ready();
  const state = app.settings();
  state.relayProfiles.push({ id: "new", modelList: targets[1], configContents: "new configuration" });
  state.activeRelayId = "new";
  app.replaceSettings(state);
  await app.window.__codexSessionDeleteBridge("/settings/get", {});
  const profile = app.settings().relayProfiles.find((item) => item.id === "new");
  assert.ok(JSON.parse(profile.modelMetadata || "{}")[targets[1]]?.supported_reasoning_levels
    ?.some((item) => item.effort === "max"));
  assert.equal(profile.configContents, "new configuration");
  assert.equal(app.settings().activeRelayId, "new");
});

test("settings writes are normalized before persistence", async () => {
  const app = harness([]);
  await app.ready();
  await app.window.__codexSessionDeleteBridge("/settings/set", {
    relayProfiles: [{ id: "written", modelList: targets[0] }],
  });
  const entry = JSON.parse(app.settings().relayProfiles[0].modelMetadata || "{}")[targets[0]];
  assert.ok(entry?.supported_reasoning_levels?.some((item) => item.effort === "max"));
});

test("catalog UI exposes max only for exact models already listed by that provider", async () => {
  const app = harness([{ id: "ui" }], {
    models: [targets[1], "gpt-6.1-terra-other-snapshot", "another-model"],
    modelMetadata: { "another-model": { displayName: "Unchanged" } },
  });
  await app.ready();
  const catalog = await app.window.__codexSessionDeleteBridge("/codex-model-catalog", {});
  assert.ok(catalog.modelMetadata[targets[1]]?.supportedReasoningEfforts
    ?.some((item) => item.reasoningEffort === "max"));
  assert.equal(catalog.modelMetadata[targets[0]], undefined);
  assert.equal(catalog.modelMetadata["gpt-6.1-terra-other-snapshot"], undefined);
  assert.deepEqual(catalog.models, [targets[1], "gpt-6.1-terra-other-snapshot", "another-model"]);
  assert.deepEqual(catalog.modelMetadata["another-model"], { displayName: "Unchanged" });
});

test("backend bridge reconnection keeps the policy installed", async () => {
  const app = harness([]);
  await app.ready();
  const replacement = async (route) => route === "/settings/get"
    ? { relayProfiles: [] } : { models: [targets[0]] };
  app.window.__codexSessionDeleteBridge = replacement;
  const catalog = await app.window.__codexSessionDeleteBridge("/codex-model-catalog", {});
  assert.ok(catalog.modelMetadata?.[targets[0]]?.supportedReasoningEfforts
    ?.some((item) => item.reasoningEffort === "max"));
});

test("cleanup restores the current bridge and removes the installed policy", async () => {
  const app = harness([]);
  await app.ready();
  assert.equal(app.cleanups.length, 1);
  app.cleanups[0]();
  assert.equal(app.window.__codexSessionDeleteBridge, app.original);
  assert.equal(app.window.__codexPlusMaxTierPolicy, undefined);
});

test("malformed metadata is reported without discarding or echoing it", async () => {
  const app = harness([{ id: "broken", modelMetadata: "{private-broken-fixture" }]);
  await app.ready();
  assert.equal(app.writes.length, 0);
  assert.ok(app.window.__codexPlusMaxTierPolicy?.lastError);
  assert.ok(!app.window.__codexPlusMaxTierPolicy.lastError.includes("private-broken-fixture"));
  assert.equal(app.settings().relayProfiles[0].modelMetadata, "{private-broken-fixture");
});

test("case aliases cannot override the canonical native rule during generation", async () => {
  const app = harness([{
    id: "case-alias",
    modelMetadata: JSON.stringify({
      [targets[1]]: { supported_reasoning_levels: [{ effort: "high" }] },
      "GPT-6.1-TERRA": { supported_reasoning_levels: [{ effort: "high" }] },
    }),
  }]);
  await app.ready();
  const metadata = JSON.parse(app.settings().relayProfiles[0].modelMetadata);
  const matching = Object.keys(metadata).filter((key) => key.toLowerCase() === targets[1]);
  assert.deepEqual(matching, [targets[1]]);
  assert.ok(metadata[targets[1]].supported_reasoning_levels.some((level) => level.effort === "max"));
});

test("persistent metadata survives five independent document lifecycles", async () => {
  let profiles = [{ id: "persistent", modelList: targets.join("\n") }];
  for (let restart = 0; restart < 5; restart++) {
    const app = harness(profiles);
    await app.ready();
    profiles = app.settings().relayProfiles;
    for (const slug of targets) {
      const entry = JSON.parse(profiles[0].modelMetadata || "{}")[slug];
      assert.ok(entry?.supported_reasoning_levels?.some((level) => level.effort === "max"));
    }
    assert.equal(app.writes.length, restart === 0 ? 1 : 0);
    app.cleanups[0]();
  }
});

test("cleanup preserves a reconnected bridge instead of restoring a stale one", async () => {
  const app = harness([]);
  await app.ready();
  const replacement = async () => ({ relayProfiles: [] });
  app.window.__codexSessionDeleteBridge = replacement;
  app.cleanups[0]();
  assert.equal(app.window.__codexSessionDeleteBridge, replacement);
});
