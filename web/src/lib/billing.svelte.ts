/** Billing state shared across the app. Everything is free until the server says PRO_REQUIRED=1;
 *  then accounts with plan 'free' are limited to FREE_RIFLES / FREE_AMMO profiles and see the upgrade button. */
export const FREE_RIFLES = 1;
export const FREE_AMMO = 3;
export const PRO_PRICE = "$5 one-time";

type Billing = { required: boolean; priceId: string | null; clientToken: string | null; env: "sandbox" | "production" };
type User = { id: string; email: string; name: string; plan: string; pro: boolean } | null;

class BillingStore {
  user = $state<User>(null);
  billing = $state<Billing>({ required: false, priceId: null, clientToken: null, env: "production" });
  /** True when profile limits apply to this person right now. */
  get limited() { return this.billing.required && !(this.user?.pro); }
  get canUpgrade() { return this.billing.required && !!this.user && !this.user.pro && !!this.billing.clientToken && !!this.billing.priceId; }
  set(user: User, billing: Billing) { this.user = user; this.billing = billing; }
}
export const billing = new BillingStore();

declare global { interface Window { Paddle?: any } }
let loading: Promise<void> | null = null;
function loadPaddle(): Promise<void> {
  if (window.Paddle) return Promise.resolve();
  if (!loading) loading = new Promise((res, rej) => {
    const s = document.createElement("script"); s.src = "https://cdn.paddle.com/paddle/v2/paddle.js"; s.async = true;
    s.onload = () => res(); s.onerror = () => rej(new Error("paddle_load")); document.head.appendChild(s);
  });
  return loading;
}

/** Opens Paddle checkout for the signed-in user. Resolves when the checkout reports completion (payment accepted). */
export async function openCheckout(): Promise<boolean> {
  const u = billing.user, b = billing.billing;
  if (!u || !b.clientToken || !b.priceId) return false;
  await loadPaddle();
  return new Promise((resolve) => {
    const P = window.Paddle;
    if (b.env === "sandbox") P.Environment.set("sandbox");
    P.Initialize({ token: b.clientToken, eventCallback: (e: any) => { if (e?.name === "checkout.completed") resolve(true); if (e?.name === "checkout.closed") resolve(false); } });
    P.Checkout.open({ items: [{ priceId: b.priceId, quantity: 1 }], customData: { account_id: u.id }, customer: { email: u.email },
      settings: { displayMode: "overlay", theme: "dark", successUrl: undefined } });
  });
}
