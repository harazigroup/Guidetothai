# Online payments for the airport arrival booking (/vip-booking/)

The booking page sends the details to a small Supabase Edge Function (`functions/gtt-checkout`),
which creates a Stripe Checkout session with the price set on the server (VIP ฿6,000, Standard ฿1,500 per person)
and shows the Stripe payment form inside the page.

## Switch payments on (one time)
1. **Supabase** (project `lmwpilpcuxyzpygylclq`) → Edge Functions → *Deploy a new function* → name it `gtt-checkout`,
   paste `functions/gtt-checkout/index.ts`, and turn **OFF "Verify JWT"**.
2. Supabase → Edge Functions → **Secrets** → add `GTT_STRIPE_SECRET_KEY` = the secret key (`sk_live_…`) of the
   Stripe account that should receive the money.
3. In `site.yml` paste the matching **publishable** key (`pk_live_…`) into `payments.stripe_publishable_key` and commit.

Until step 3 is done, the form still works: it sends the booking details to WhatsApp instead of taking payment.

## Where to see bookings
Stripe → Payments. Each payment shows the booking ref (GTT-VIP-… / GTT-STD-…) and, under Metadata,
name, WhatsApp, flight, date/time, airport, travellers, hotel, bags and notes. Stripe emails the customer a receipt.

## Change prices
Edit `PACKAGES` in `functions/gtt-checkout/index.ts` (and the prices shown in `content/pages/*/vip-booking.html`,
`content/pages/*/vip-airport.html` and `assets/js/vip-checkout.js`), then redeploy the function.
