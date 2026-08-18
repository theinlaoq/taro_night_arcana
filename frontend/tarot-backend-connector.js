// TarotBackendConnector — the single boundary between the UI and the Tarot domain.
// The frontend must never reach past this file: no deck, no shuffling, no reversal
// probability, no verdict logic, no prompts, no LLM calls.
//
// EXTERNAL CONNECTOR
// Talks to the production REST API.
//
// Expected production contract:
//   POST   /api/tarot/sessions              -> createSession({ spreadId, reversals })
//   POST   /api/tarot/sessions/{id}/draw    -> drawCard({ sessionId, slot })
//   POST   /api/tarot/sessions/{id}/interpret -> interpret({ sessionId, question, tone })
//   DELETE /api/tarot/sessions/{id}         -> resetSession({ sessionId })
//
// Errors are surfaced as { code, message }; the UI branches on `code` only.

(function () {
  const LOCAL_DEV_API =
    (location.hostname === "127.0.0.1" || location.hostname === "localhost") &&
    location.port === "5173"
      ? "http://127.0.0.1:8000"
      : "";
  const API_BASE = String(window.TAROT_BACKEND_URL || LOCAL_DEV_API).replace(/\/+$/, "");

  // Accepts { code, message }, { error: { code, message } }, a plain Error, or anything else.
  // Always yields { code, message }; a known code is never downgraded to UNKNOWN_ERROR.
  function normalizeError(e) {
    if (e && typeof e === "object") {
      if (typeof e.code === "string" && e.code) {
        return { code: e.code, message: e.message || e.code };
      }
      if (e.error && typeof e.error === "object" && typeof e.error.code === "string" && e.error.code) {
        return { code: e.error.code, message: e.error.message || e.error.code };
      }
    }
    if (typeof e === "string" && e) return { code: "UNKNOWN_ERROR", message: e };
    return { code: "UNKNOWN_ERROR", message: (e && e.message) || "Unknown error" };
  }

  async function request(path, options) {
    let res;
    try {
      res = await fetch(API_BASE + path, options);
    } catch (e) {
      throw normalizeError({ code: "BACKEND_UNAVAILABLE", message: "Backend is not reachable" });
    }

    let body = null;
    try {
      body = await res.json();
    } catch (e) {
      body = null;
    }

    if (!res.ok) {
      throw normalizeError(body || { code: "UNKNOWN_ERROR", message: res.statusText });
    }

    return body;
  }

  function post(path, payload) {
    return request(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload || {}),
    });
  }

  function normalizeImageUrl(card) {
    if (!card || !card.imageUrl) return card;
    if (!API_BASE || /^https?:\/\//i.test(card.imageUrl)) return card;
    return Object.assign({}, card, {
      imageUrl: new URL(card.imageUrl, API_BASE + "/").href,
    });
  }

  function normalizeDrawResponse(res) {
    if (!res || !res.card) return res;
    return Object.assign({}, res, { card: normalizeImageUrl(res.card) });
  }

  function sessionPath(sessionId, suffix) {
    return "/api/tarot/sessions/" + encodeURIComponent(sessionId) + suffix;
  }

  async function remove(path) {
    return request(path, { method: "DELETE" });
  }

  async function call(method, payload) {
    try {
      if (method === "createSession") {
        return await post("/api/tarot/sessions", payload);
      }
      if (method === "drawCard") {
        const res = await post(sessionPath(payload.sessionId, "/draw"), { slot: payload.slot });
        return normalizeDrawResponse(res);
      }
      if (method === "interpret") {
        return await post(sessionPath(payload.sessionId, "/interpret"), {
          question: payload.question || "",
          tone: payload.tone || "warm",
        });
      }
      if (method === "resetSession") {
        return await remove(sessionPath(payload.sessionId, ""));
      }
      throw { code: "UNKNOWN_ERROR", message: "Unknown connector method" };
    } catch (e) {
      throw normalizeError(e);
    }
  }

  window.TarotBackendConnector = {
    // -> { sessionId, spread: { id, name, cardsRequired, positions: [{ index, name }] }, deck: { size } }
    createSession: ({ spreadId, reversals }) => call("createSession", { spreadId, reversals }),

    // -> { position: { index, name }, card: { id, name, reversed, imageUrl, meaning, arcana, element }, verdict?, verdictText? }
    // drawCard is idempotent for the pair (sessionId, slot).
    // Repeated calls for the same slot must return the original draw result.
    drawCard: ({ sessionId, slot }) => call("drawCard", { sessionId, slot }),

    // -> { type: "ai" | "basic", text, reason? }
    interpret: ({ sessionId, question, tone }) => call("interpret", { sessionId, question, tone }),

    // -> { ok: true }
    resetSession: ({ sessionId }) => call("resetSession", { sessionId }),
  };
})();
