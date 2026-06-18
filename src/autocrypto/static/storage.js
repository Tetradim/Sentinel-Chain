(function () {
  "use strict";

  const STRATEGY_PIN_STORAGE_KEY = "autoCryptoPinnedStrategies";
  const STRATEGY_BACKTEST_STORAGE_KEY = "autoCryptoBacktests";
  const TICKET_DRAFT_STORAGE_KEY = "autoCryptoTicketDraft";
  const AUTO_REFRESH_STORAGE_KEY = "autoCryptoAutoRefresh";
  const IMPORTED_STRATEGY_STORAGE_KEY = "autoCryptoImportedStrategy";

  function readJson(key, fallback) {
    try {
      const stored = localStorage.getItem(key);
      if (stored === null) return fallback;
      return JSON.parse(stored);
    } catch {
      return fallback;
    }
  }

  function readObject(key) {
    const parsed = readJson(key, null);
    return parsed && typeof parsed === "object" && !Array.isArray(parsed) ? parsed : null;
  }

  function readPinnedStrategies() {
    const parsed = readJson(STRATEGY_PIN_STORAGE_KEY, []);
    return new Set(Array.isArray(parsed) ? parsed.filter(Boolean) : []);
  }

  function writePinnedStrategies(pinned) {
    localStorage.setItem(STRATEGY_PIN_STORAGE_KEY, JSON.stringify([...pinned]));
  }

  function readStoredBacktests() {
    return readObject(STRATEGY_BACKTEST_STORAGE_KEY) || {};
  }

  function writeStoredBacktests(backtests) {
    localStorage.setItem(STRATEGY_BACKTEST_STORAGE_KEY, JSON.stringify(backtests || {}));
  }

  function readStoredTicketDraft() {
    return readObject(TICKET_DRAFT_STORAGE_KEY);
  }

  function writeStoredTicketDraft(draft) {
    localStorage.setItem(TICKET_DRAFT_STORAGE_KEY, JSON.stringify(draft));
  }

  function clearStoredTicketDraft() {
    localStorage.removeItem(TICKET_DRAFT_STORAGE_KEY);
  }

  function readAutoRefreshEnabled() {
    return localStorage.getItem(AUTO_REFRESH_STORAGE_KEY) === "true";
  }

  function writeAutoRefreshEnabled(enabled) {
    localStorage.setItem(AUTO_REFRESH_STORAGE_KEY, enabled ? "true" : "false");
  }

  function readImportedStrategy() {
    return readObject(IMPORTED_STRATEGY_STORAGE_KEY);
  }

  function writeImportedStrategy(strategy) {
    localStorage.setItem(IMPORTED_STRATEGY_STORAGE_KEY, JSON.stringify(strategy));
  }

  window.AutoCryptoStorage = {
    STRATEGY_PIN_STORAGE_KEY,
    STRATEGY_BACKTEST_STORAGE_KEY,
    TICKET_DRAFT_STORAGE_KEY,
    AUTO_REFRESH_STORAGE_KEY,
    IMPORTED_STRATEGY_STORAGE_KEY,
    readPinnedStrategies,
    writePinnedStrategies,
    readStoredBacktests,
    writeStoredBacktests,
    readStoredTicketDraft,
    writeStoredTicketDraft,
    clearStoredTicketDraft,
    readAutoRefreshEnabled,
    writeAutoRefreshEnabled,
    readImportedStrategy,
    writeImportedStrategy,
  };
})();
