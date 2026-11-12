// Waits out per-minute provider rate limits (for example "Rate limit of 2000
// per 60s exceeded for UserByModelByMinute") instead of failing the session.
// It does not raise the provider's cap; it paces requests so work continues
// after the window resets. OpenCode's built-in maximum attempt count still
// applies.
const RATE_LIMIT = /rate.?limit|too many requests|ByMinute|429/i;
const WAIT_HINT = /(?:wait|retry(?:ing)?(?:\s+after|\s+in)?)\s+(\d+)\s*(?:s\b|sec|second)/i;
const DEFAULT_WAIT_SECONDS = 62;
const MAX_WAIT_SECONDS = 120;

export const waitSeconds = (message) => {
  const hinted = Number(WAIT_HINT.exec(message ?? "")?.[1]);
  const seconds = Number.isFinite(hinted) && hinted > 0 ? hinted + 2 : DEFAULT_WAIT_SECONDS;
  return Math.min(seconds, MAX_WAIT_SECONDS);
};

export const isRateLimit = (error) =>
  error?.status === 429 || RATE_LIMIT.test(`${error?.type ?? ""} ${error?.message ?? ""}`);

export default {
  id: "rate-limit-wait",

  async setup(ctx) {
    await ctx.session.hook("retry", (event) => {
      if (!isRateLimit(event.error)) return;
      event.decision = { retry: true, delay: waitSeconds(event.error.message) * 1000 };
    });
  },

  async server() {
    return {};
  },
};
